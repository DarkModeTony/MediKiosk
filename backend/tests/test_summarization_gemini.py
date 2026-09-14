import os
import json
import pytest
from unittest.mock import patch, MagicMock
from ai.summarization.models import ClinicalSummaryInput, SourceType
from ai.summarization.service import get_summary_provider
from ai.summarization.gemini_provider import GeminiSummaryProvider

@pytest.fixture
def mock_gemini():
    with patch("ai.summarization.gemini_provider.genai.Client") as mock:
        yield mock

def _create_mock_response(structured_sections, source_references, refusal=None, invalid_json=False):
    mock_resp = MagicMock()
    if refusal:
        mock_resp.text = ""
        return mock_resp
    if invalid_json:
        mock_resp.text = "{ invalid json"
        return mock_resp

    data = {
        "structured_sections": [{"title": s.title, "content": s.content} for s in structured_sections],
        "source_references": [{"source_type": r.source_type, "source_id": r.source_id, "fact": r.fact} for r in source_references]
    }
    mock_resp.text = json.dumps(data)
    return mock_resp

def test_ai_mode_real_routing_gemini(monkeypatch):
    monkeypatch.setenv("AI_MODE", "real")
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    provider = get_summary_provider()
    assert isinstance(provider, GeminiSummaryProvider)

def test_ai_mode_real_routing_missing_provider(monkeypatch):
    monkeypatch.setenv("AI_MODE", "real")
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    with pytest.raises(ValueError, match="missing or unsupported"):
        get_summary_provider()

def test_ai_mode_real_routing_unsupported_provider(monkeypatch):
    monkeypatch.setenv("AI_MODE", "real")
    monkeypatch.setenv("LLM_PROVIDER", "unknown")
    with pytest.raises(ValueError, match="missing or unsupported"):
        get_summary_provider()

def test_valid_llm_response(mock_gemini):
    os.environ["GEMINI_API_KEY"] = "test-key"
    provider = GeminiSummaryProvider()
    
    input_data = ClinicalSummaryInput(
        chief_complaint="Patient presents with headache",
        symptoms=["headache", "nausea"],
        medications=["Tylenol 500mg"]
    )
    
    sec1 = MagicMock(title="HPI", content="Patient has a headache and nausea. Takes Tylenol 500mg.")
    ref1 = MagicMock(source_type=SourceType.CLINICAL_INTERVIEW.value, source_id="123", fact="headache")
    
    provider.client.models.generate_content.return_value = _create_mock_response([sec1], [ref1])
    
    draft = provider.generate(input_data)
    assert draft.status == "AI_DRAFT"
    assert len(draft.structured_sections) == 1
    assert "Tylenol" in draft.structured_sections[0].content

def test_hallucinated_diagnosis_rejected(mock_gemini):
    os.environ["GEMINI_API_KEY"] = "test-key"
    provider = GeminiSummaryProvider()
    input_data = ClinicalSummaryInput(symptoms=["headache"])
    sec1 = MagicMock(title="HPI", content="Patient complains of headache. Diagnosed with hypertension.")
    provider.client.models.generate_content.return_value = _create_mock_response([sec1], [])
    with pytest.raises(RuntimeError, match="Anti-hallucination validation failed"):
        provider.generate(input_data)

def test_hallucinated_medication_rejected(mock_gemini):
    provider = GeminiSummaryProvider()
    input_data = ClinicalSummaryInput(symptoms=["headache"])
    sec1 = MagicMock(title="Meds", content="Patient takes Amlodipine")
    provider.client.models.generate_content.return_value = _create_mock_response([sec1], [])
    with pytest.raises(RuntimeError, match="Anti-hallucination validation failed"):
        provider.generate(input_data)

def test_hallucinated_medication_dose_rejected(mock_gemini):
    provider = GeminiSummaryProvider()
    input_data = ClinicalSummaryInput(medications=["Amlodipine"])
    sec1 = MagicMock(title="Meds", content="Amlodipine 10mg daily")
    provider.client.models.generate_content.return_value = _create_mock_response([sec1], [])
    with pytest.raises(RuntimeError, match="Anti-hallucination validation failed"):
        provider.generate(input_data)

def test_hallucinated_laboratory_value_rejected(mock_gemini):
    provider = GeminiSummaryProvider()
    input_data = ClinicalSummaryInput()
    sec1 = MagicMock(title="Labs", content="Hemoglobin is 14.2 g/dL")
    provider.client.models.generate_content.return_value = _create_mock_response([sec1], [])
    with pytest.raises(RuntimeError, match="Anti-hallucination validation failed"):
        provider.generate(input_data)

def test_hallucinated_symptom_rejected(mock_gemini):
    provider = GeminiSummaryProvider()
    input_data = ClinicalSummaryInput()
    sec1 = MagicMock(title="HPI", content="Patient has severe chest pain")
    provider.client.models.generate_content.return_value = _create_mock_response([sec1], [])
    with pytest.raises(RuntimeError, match="Anti-hallucination validation failed"):
        provider.generate(input_data)

def test_hallucinated_procedure_rejected(mock_gemini):
    provider = GeminiSummaryProvider()
    input_data = ClinicalSummaryInput()
    sec1 = MagicMock(title="HPI", content="Underwent appendectomy")
    provider.client.models.generate_content.return_value = _create_mock_response([sec1], [])
    with pytest.raises(RuntimeError, match="Anti-hallucination validation failed"):
        provider.generate(input_data)

def test_hallucinated_vital_rejected(mock_gemini):
    provider = GeminiSummaryProvider()
    input_data = ClinicalSummaryInput()
    sec1 = MagicMock(title="Vitals", content="Blood pressure 120/80")
    provider.client.models.generate_content.return_value = _create_mock_response([sec1], [])
    with pytest.raises(RuntimeError, match="Anti-hallucination validation failed"):
        provider.generate(input_data)

def test_hallucinated_allergy_rejected(mock_gemini):
    provider = GeminiSummaryProvider()
    input_data = ClinicalSummaryInput()
    sec1 = MagicMock(title="Allergies", content="Allergic to Penicillin")
    provider.client.models.generate_content.return_value = _create_mock_response([sec1], [])
    with pytest.raises(RuntimeError, match="Anti-hallucination validation failed"):
        provider.generate(input_data)

def test_hallucinated_date_rejected(mock_gemini):
    provider = GeminiSummaryProvider()
    input_data = ClinicalSummaryInput(symptoms=["fever"])
    sec1 = MagicMock(title="HPI", content="Fever started on 2024-01-05")
    provider.client.models.generate_content.return_value = _create_mock_response([sec1], [])
    with pytest.raises(RuntimeError, match="Anti-hallucination validation failed"):
        provider.generate(input_data)

def test_hallucinated_source_reference_rejected(mock_gemini):
    provider = GeminiSummaryProvider()
    input_data = ClinicalSummaryInput(symptoms=["headache"])
    sec1 = MagicMock(title="HPI", content="headache")
    ref1 = MagicMock(source_type=SourceType.CLINICAL_INTERVIEW.value, source_id="123", fact="hypertension")
    provider.client.models.generate_content.return_value = _create_mock_response([sec1], [ref1])
    with pytest.raises(RuntimeError, match="Source reference validation failed"):
        provider.generate(input_data)

def test_invalid_json_schema_rejected(mock_gemini):
    provider = GeminiSummaryProvider()
    input_data = ClinicalSummaryInput()
    provider.client.models.generate_content.return_value = _create_mock_response([], [], invalid_json=True)
    with pytest.raises(RuntimeError, match="LLM returned invalid schema"):
        provider.generate(input_data)

def test_empty_clinical_input(mock_gemini):
    provider = GeminiSummaryProvider()
    input_data = ClinicalSummaryInput()
    sec1 = MagicMock(title="HPI", content="Not documented")
    provider.client.models.generate_content.return_value = _create_mock_response([sec1], [])
    draft = provider.generate(input_data)
    assert draft.structured_sections[0].content == "Not documented"

def test_existing_red_flag_remains_unchanged(mock_gemini):
    provider = GeminiSummaryProvider()
    input_data = ClinicalSummaryInput(red_flags=[{"severity": "HIGH", "rule_name": "Chest Pain"}])
    sec1 = MagicMock(title="Red Flags", content="Priority HIGH detected by rules for Chest Pain")
    provider.client.models.generate_content.return_value = _create_mock_response([sec1], [])
    draft = provider.generate(input_data)
    assert len(draft.structured_sections) == 1
    assert "Chest Pain" in draft.structured_sections[0].content

def test_api_failure_safely_handled(mock_gemini):
    provider = GeminiSummaryProvider()
    input_data = ClinicalSummaryInput()
    provider.client.models.generate_content.side_effect = Exception("Connection Timeout")
    with pytest.raises(RuntimeError, match="Failed to generate LLM summary"):
        provider.generate(input_data)
