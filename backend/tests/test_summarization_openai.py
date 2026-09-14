import os
import pytest
from unittest.mock import patch, MagicMock
from ai.summarization.models import ClinicalSummaryInput, SourceType
from ai.summarization.service import get_summary_provider
from ai.summarization.mock_provider import MockSummaryProvider
from ai.summarization.openai_provider import OpenAISummaryProvider
from pydantic import ValidationError

@pytest.fixture
def mock_openai():
    with patch("ai.summarization.openai_provider.OpenAI") as mock:
        yield mock

def _create_mock_response(structured_sections, source_references, refusal=None):
    mock_msg = MagicMock()
    mock_msg.refusal = refusal
    if not refusal:
        mock_parsed = MagicMock()
        mock_parsed.structured_sections = structured_sections
        mock_parsed.source_references = source_references
        mock_msg.parsed = mock_parsed
    else:
        mock_msg.parsed = None
    
    mock_choice = MagicMock()
    mock_choice.message = mock_msg
    
    mock_resp = MagicMock()
    mock_resp.choices = [mock_choice]
    return mock_resp

def test_ai_mode_mock_routing():
    os.environ["AI_MODE"] = "mock"
    provider = get_summary_provider()
    assert isinstance(provider, MockSummaryProvider)

def test_ai_mode_real_routing_openai(monkeypatch):
    monkeypatch.setenv("AI_MODE", "real")
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    provider = get_summary_provider()
    assert isinstance(provider, OpenAISummaryProvider)

def test_valid_llm_response(mock_openai):
    os.environ["OPENAI_API_KEY"] = "test-key"
    provider = OpenAISummaryProvider()
    
    input_data = ClinicalSummaryInput(
        chief_complaint="Patient presents with headache",
        symptoms=["headache", "nausea"],
        medications=["Tylenol 500mg"]
    )
    
    sec1 = MagicMock(title="HPI", content="Patient has a headache and nausea. Takes Tylenol 500mg.")
    ref1 = MagicMock(source_type=SourceType.CLINICAL_INTERVIEW, source_id="123", fact="headache")
    
    provider.client.beta.chat.completions.parse.return_value = _create_mock_response([sec1], [ref1])
    
    draft = provider.generate(input_data)
    assert draft.status == "AI_DRAFT"
    assert len(draft.structured_sections) == 1
    assert "Tylenol" in draft.structured_sections[0].content

def test_hallucinated_diagnosis_rejected(mock_openai):
    os.environ["OPENAI_API_KEY"] = "test-key"
    provider = OpenAISummaryProvider()
    
    input_data = ClinicalSummaryInput(symptoms=["headache"])
    
    # LLM hallucinates hypertension
    sec1 = MagicMock(title="HPI", content="Patient complains of headache. Diagnosed with hypertension.")
    provider.client.beta.chat.completions.parse.return_value = _create_mock_response([sec1], [])
    
    with pytest.raises(RuntimeError, match="Anti-hallucination validation failed"):
        provider.generate(input_data)

def test_hallucinated_medication_rejected(mock_openai):
    provider = OpenAISummaryProvider()
    input_data = ClinicalSummaryInput(symptoms=["headache"])
    sec1 = MagicMock(title="Meds", content="Patient takes Amlodipine")
    provider.client.beta.chat.completions.parse.return_value = _create_mock_response([sec1], [])
    
    with pytest.raises(RuntimeError, match="Anti-hallucination validation failed"):
        provider.generate(input_data)

def test_hallucinated_medication_dose_rejected(mock_openai):
    provider = OpenAISummaryProvider()
    input_data = ClinicalSummaryInput(medications=["Amlodipine"])
    sec1 = MagicMock(title="Meds", content="Amlodipine 10mg daily")
    provider.client.beta.chat.completions.parse.return_value = _create_mock_response([sec1], [])
    # 10mg is not in input
    with pytest.raises(RuntimeError, match="Anti-hallucination validation failed"):
        provider.generate(input_data)

def test_hallucinated_laboratory_value_rejected(mock_openai):
    provider = OpenAISummaryProvider()
    input_data = ClinicalSummaryInput()
    sec1 = MagicMock(title="Labs", content="Hemoglobin is 14.2 g/dL")
    provider.client.beta.chat.completions.parse.return_value = _create_mock_response([sec1], [])
    with pytest.raises(RuntimeError, match="Anti-hallucination validation failed"):
        provider.generate(input_data)

def test_hallucinated_symptom_rejected(mock_openai):
    provider = OpenAISummaryProvider()
    input_data = ClinicalSummaryInput()
    sec1 = MagicMock(title="HPI", content="Patient has severe chest pain")
    provider.client.beta.chat.completions.parse.return_value = _create_mock_response([sec1], [])
    with pytest.raises(RuntimeError, match="Anti-hallucination validation failed"):
        provider.generate(input_data)

def test_hallucinated_procedure_rejected(mock_openai):
    provider = OpenAISummaryProvider()
    input_data = ClinicalSummaryInput()
    sec1 = MagicMock(title="HPI", content="Underwent appendectomy")
    provider.client.beta.chat.completions.parse.return_value = _create_mock_response([sec1], [])
    with pytest.raises(RuntimeError, match="Anti-hallucination validation failed"):
        provider.generate(input_data)

def test_hallucinated_vital_rejected(mock_openai):
    provider = OpenAISummaryProvider()
    input_data = ClinicalSummaryInput()
    sec1 = MagicMock(title="Vitals", content="Blood pressure 120/80")
    provider.client.beta.chat.completions.parse.return_value = _create_mock_response([sec1], [])
    with pytest.raises(RuntimeError, match="Anti-hallucination validation failed"):
        provider.generate(input_data)

def test_hallucinated_allergy_rejected(mock_openai):
    provider = OpenAISummaryProvider()
    input_data = ClinicalSummaryInput()
    sec1 = MagicMock(title="Allergies", content="Allergic to Penicillin")
    provider.client.beta.chat.completions.parse.return_value = _create_mock_response([sec1], [])
    with pytest.raises(RuntimeError, match="Anti-hallucination validation failed"):
        provider.generate(input_data)

def test_hallucinated_date_rejected(mock_openai):
    provider = OpenAISummaryProvider()
    input_data = ClinicalSummaryInput(symptoms=["fever"])
    sec1 = MagicMock(title="HPI", content="Fever started on 2024-01-05")
    provider.client.beta.chat.completions.parse.return_value = _create_mock_response([sec1], [])
    with pytest.raises(RuntimeError, match="Anti-hallucination validation failed"):
        provider.generate(input_data)

def test_hallucinated_source_reference_rejected(mock_openai):
    provider = OpenAISummaryProvider()
    input_data = ClinicalSummaryInput(symptoms=["headache"])
    sec1 = MagicMock(title="HPI", content="headache")
    # fact="hypertension" is not in input
    ref1 = MagicMock(source_type=SourceType.CLINICAL_INTERVIEW, source_id="123", fact="hypertension")
    provider.client.beta.chat.completions.parse.return_value = _create_mock_response([sec1], [ref1])
    with pytest.raises(RuntimeError, match="Source reference validation failed"):
        provider.generate(input_data)

def test_invalid_json_schema_rejected(mock_openai):
    provider = OpenAISummaryProvider()
    input_data = ClinicalSummaryInput()
    # Mock validation error from API
    provider.client.beta.chat.completions.parse.side_effect = ValidationError.from_exception_data("error", line_errors=[])
    with pytest.raises(RuntimeError, match="LLM returned invalid schema"):
        provider.generate(input_data)

def test_empty_clinical_input(mock_openai):
    provider = OpenAISummaryProvider()
    input_data = ClinicalSummaryInput()
    sec1 = MagicMock(title="HPI", content="Not documented")
    provider.client.beta.chat.completions.parse.return_value = _create_mock_response([sec1], [])
    draft = provider.generate(input_data)
    assert draft.structured_sections[0].content == "Not documented"

def test_existing_red_flag_remains_unchanged(mock_openai):
    provider = OpenAISummaryProvider()
    input_data = ClinicalSummaryInput(red_flags=[{"severity": "HIGH", "rule_name": "Chest Pain"}])
    sec1 = MagicMock(title="Red Flags", content="Priority HIGH detected by rules for Chest Pain")
    provider.client.beta.chat.completions.parse.return_value = _create_mock_response([sec1], [])
    draft = provider.generate(input_data)
    assert len(draft.structured_sections) == 1
    assert "Chest Pain" in draft.structured_sections[0].content

def test_supported_paraphrasing_accepted(mock_openai):
    provider = OpenAISummaryProvider()
    input_data = ClinicalSummaryInput(symptoms=["fever", "cough"])
    # LLM paraphrases "fever" and "cough" into "patient presents with fever and coughing"
    sec1 = MagicMock(title="HPI", content="Patient presents with fever and cough")
    provider.client.beta.chat.completions.parse.return_value = _create_mock_response([sec1], [])
    draft = provider.generate(input_data)
    assert draft.structured_sections[0].content == "Patient presents with fever and cough"

def test_unsupported_new_clinical_entity_rejected(mock_openai):
    provider = OpenAISummaryProvider()
    input_data = ClinicalSummaryInput(symptoms=["fever"])
    # "diabetes" is an unsupported entity
    sec1 = MagicMock(title="HPI", content="Fever and diabetes")
    provider.client.beta.chat.completions.parse.return_value = _create_mock_response([sec1], [])
    with pytest.raises(RuntimeError, match="Anti-hallucination validation failed"):
        provider.generate(input_data)

def test_api_failure_safely_handled(mock_openai):
    provider = OpenAISummaryProvider()
    input_data = ClinicalSummaryInput()
    provider.client.beta.chat.completions.parse.side_effect = Exception("Connection Timeout")
    with pytest.raises(RuntimeError, match="Failed to generate LLM summary"):
        provider.generate(input_data)

def test_rejected_ocr_entity_excluded():
    from ai.summarization.aggregator import ClinicalDataAggregator
    from app.models.models import Encounter, Document, DocumentEntity
    
    mock_db = MagicMock()
    # Mock the queries
    mock_encounter_query = MagicMock()
    mock_encounter = Encounter(id="123")
    mock_encounter_query.filter.return_value.first.return_value = mock_encounter
    
    mock_history_query = MagicMock()
    mock_history_query.filter.return_value.first.return_value = None
    
    mock_symptom_query = MagicMock()
    mock_symptom_query.filter.return_value.all.return_value = []
    
    mock_rf_query = MagicMock()
    mock_rf_query.filter.return_value.all.return_value = []
    
    mock_doc_query = MagicMock()
    mock_doc = Document(id="doc1", doc_type="PRESCRIPTION")
    mock_doc_query.filter.return_value.all.return_value = [mock_doc]
    
    mock_ent_query = MagicMock()
    valid_ent = DocumentEntity(id="ent1", status="AI_EXTRACTED", entity_type="MEDICATION", value={"name": "Amlodipine"})
    rejected_ent = DocumentEntity(id="ent2", status="REJECTED", entity_type="MEDICATION", value={"name": "Lisinopril"})
    mock_ent_query.filter.return_value.all.return_value = [valid_ent, rejected_ent]
    
    def mock_query(model):
        if model == Encounter:
            return mock_encounter_query
        elif model.__name__ == "ClinicalHistory":
            return mock_history_query
        elif model.__name__ == "Symptom":
            return mock_symptom_query
        elif model.__name__ == "RedFlag":
            return mock_rf_query
        elif model.__name__ == "Document":
            return mock_doc_query
        elif model.__name__ == "DocumentEntity":
            return mock_ent_query
    
    mock_db.query.side_effect = mock_query
    
    agg = ClinicalDataAggregator(mock_db)
    input_data, refs = agg.gather_data("123")
    
    assert any("Amlodipine" in m for m in input_data.medications)
    assert not any("Lisinopril" in m for m in input_data.medications)
