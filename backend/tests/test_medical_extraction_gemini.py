import os
import pytest
from unittest.mock import MagicMock, patch
from ai.medical_extraction.gemini_provider import GeminiExtractionProvider, conservative_normalize
from ai.medical_extraction.service import get_extraction_provider
from ai.medical_extraction.models import ExtractedEntities, MedicationEntity, LabResult, DiagnosisEntity, GenericEntity, ConfidenceLevel

@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake_key")

@pytest.fixture
def mock_genai_client():
    with patch("ai.medical_extraction.gemini_provider.genai.Client") as mock_client:
        yield mock_client

def test_missing_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="GEMINI_API_KEY environment variable is missing"):
        GeminiExtractionProvider()

def test_empty_ocr_input(mock_env):
    provider = GeminiExtractionProvider()
    result = provider.extract("   \n", 1)
    assert not result.medications
    assert not result.lab_results
    assert not result.diagnoses

def test_whitespace_normalization():
    assert conservative_normalize("Amlodipine\n5 mg") == "amlodipine 5 mg"
    assert conservative_normalize("10 / 09 / 2026") == "10 / 09 / 2026"
    assert conservative_normalize(" Glucose: 145 ") == "glucose: 145"
    assert conservative_normalize("") == ""

def create_mock_response(mock_client, entities: ExtractedEntities):
    mock_instance = mock_client.return_value
    mock_response = MagicMock()
    mock_response.text = entities.model_dump_json()
    mock_instance.models.generate_content.return_value = mock_response

def test_valid_medication_extraction(mock_env, mock_genai_client):
    ocr_text = "Patient took Amlodipine 5 mg once daily with water."
    ent = ExtractedEntities(
        medications=[MedicationEntity(name="Amlodipine", strength="5 mg", frequency="once daily", source_text="Amlodipine 5 mg once daily")]
    )
    create_mock_response(mock_genai_client, ent)
    provider = GeminiExtractionProvider()
    res = provider.extract(ocr_text, 1)
    assert len(res.medications) == 1
    assert res.medications[0].name == "Amlodipine"
    assert res.medications[0].strength == "5 mg"
    assert res.medications[0].frequency == "once daily"
    assert res.medications[0].confidence_level == ConfidenceLevel.HIGH

def test_medication_strength_and_frequency(mock_env, mock_genai_client):
    ocr_text = "Metformin 500 mg BD"
    ent = ExtractedEntities(
        medications=[MedicationEntity(name="Metformin", strength="500 mg", frequency="BD", source_text="Metformin 500 mg BD")]
    )
    create_mock_response(mock_genai_client, ent)
    provider = GeminiExtractionProvider()
    res = provider.extract(ocr_text, 1)
    assert len(res.medications) == 1
    assert res.medications[0].strength == "500 mg"
    assert res.medications[0].frequency == "BD"

def test_explicit_diagnosis(mock_env, mock_genai_client):
    ocr_text = "Diagnosis: Hypertension and Type 2 Diabetes"
    ent = ExtractedEntities(
        diagnoses=[DiagnosisEntity(diagnosis="Hypertension", source_text="Hypertension")]
    )
    create_mock_response(mock_genai_client, ent)
    provider = GeminiExtractionProvider()
    res = provider.extract(ocr_text, 1)
    assert len(res.diagnoses) == 1
    assert res.diagnoses[0].diagnosis == "Hypertension"

def test_explicit_allergy(mock_env, mock_genai_client):
    ocr_text = "Allergies: Penicillin"
    ent = ExtractedEntities(
        other=[GenericEntity(value="Penicillin", source_text="Allergies: Penicillin")]
    )
    create_mock_response(mock_genai_client, ent)
    provider = GeminiExtractionProvider()
    res = provider.extract(ocr_text, 1)
    assert len(res.other) == 1
    assert "Penicillin" in res.other[0].value

def test_explicit_lab_value(mock_env, mock_genai_client):
    ocr_text = "HbA1c: 7.2 %"
    ent = ExtractedEntities(
        lab_results=[LabResult(test_name="HbA1c", value="7.2", unit="%", source_text="HbA1c: 7.2 %")]
    )
    create_mock_response(mock_genai_client, ent)
    provider = GeminiExtractionProvider()
    res = provider.extract(ocr_text, 1)
    assert len(res.lab_results) == 1
    assert res.lab_results[0].test_name == "HbA1c"
    assert res.lab_results[0].value == "7.2"
    assert res.lab_results[0].unit == "%"
    
def test_explicit_lab_reference_range(mock_env, mock_genai_client):
    ocr_text = "Glucose 100 mg/dL (70-110)"
    ent = ExtractedEntities(
        lab_results=[LabResult(test_name="Glucose", value="100", unit="mg/dL", reference_low="70", reference_high="110", source_text="Glucose 100 mg/dL (70-110)")]
    )
    create_mock_response(mock_genai_client, ent)
    provider = GeminiExtractionProvider()
    res = provider.extract(ocr_text, 1)
    assert len(res.lab_results) == 1
    assert res.lab_results[0].reference_low == "70"
    assert res.lab_results[0].reference_high == "110"

def test_missing_lab_reference_range(mock_env, mock_genai_client):
    ocr_text = "Glucose 100 mg/dL"
    ent = ExtractedEntities(
        lab_results=[LabResult(test_name="Glucose", value="100", unit="mg/dL", source_text="Glucose 100 mg/dL")]
    )
    create_mock_response(mock_genai_client, ent)
    provider = GeminiExtractionProvider()
    res = provider.extract(ocr_text, 1)
    assert len(res.lab_results) == 1
    assert res.lab_results[0].reference_low is None

def test_explicit_procedure(mock_env, mock_genai_client):
    ocr_text = "Procedure: ECG normal"
    ent = ExtractedEntities(
        other=[GenericEntity(value="ECG", source_text="Procedure: ECG")]
    )
    create_mock_response(mock_genai_client, ent)
    provider = GeminiExtractionProvider()
    res = provider.extract(ocr_text, 1)
    assert len(res.other) == 1
    assert res.other[0].value == "ECG"

def test_explicit_surgery(mock_env, mock_genai_client):
    ocr_text = "Surgery: Appendectomy in 2015"
    ent = ExtractedEntities(
        other=[GenericEntity(value="Appendectomy", source_text="Surgery: Appendectomy")]
    )
    create_mock_response(mock_genai_client, ent)
    provider = GeminiExtractionProvider()
    res = provider.extract(ocr_text, 1)
    assert len(res.other) == 1
    assert res.other[0].value == "Appendectomy"

def test_explicit_date(mock_env, mock_genai_client):
    ocr_text = "Date: 10/09/2026"
    ent = ExtractedEntities(document_date="10/09/2026")
    create_mock_response(mock_genai_client, ent)
    provider = GeminiExtractionProvider()
    res = provider.extract(ocr_text, 1)
    assert res.document_date == "10/09/2026"

def test_missing_date(mock_env, mock_genai_client):
    ocr_text = "Patient Name: Bob"
    ent = ExtractedEntities(document_date=None)
    create_mock_response(mock_genai_client, ent)
    provider = GeminiExtractionProvider()
    res = provider.extract(ocr_text, 1)
    assert res.document_date is None

def test_invented_diagnosis_rejected(mock_env, mock_genai_client):
    ocr_text = "Metformin 500 mg"
    ent = ExtractedEntities(
        diagnoses=[DiagnosisEntity(diagnosis="Diabetes", source_text="Diabetes")]
    )
    create_mock_response(mock_genai_client, ent)
    provider = GeminiExtractionProvider()
    res = provider.extract(ocr_text, 1)
    assert len(res.diagnoses) == 0

def test_invented_medication_rejected(mock_env, mock_genai_client):
    ocr_text = "Diagnosis: Headache"
    ent = ExtractedEntities(
        medications=[MedicationEntity(name="Aspirin", source_text="Aspirin")]
    )
    create_mock_response(mock_genai_client, ent)
    provider = GeminiExtractionProvider()
    res = provider.extract(ocr_text, 1)
    assert len(res.medications) == 0

def test_invented_medication_strength_rejected(mock_env, mock_genai_client):
    ocr_text = "Amlodipine once daily"
    ent = ExtractedEntities(
        medications=[MedicationEntity(name="Amlodipine", strength="10 mg", source_text="Amlodipine once daily")]
    )
    create_mock_response(mock_genai_client, ent)
    provider = GeminiExtractionProvider()
    res = provider.extract(ocr_text, 1)
    assert len(res.medications) == 0 # The whole entity is rejected because strength is fabricated

def test_invented_medication_frequency_rejected(mock_env, mock_genai_client):
    ocr_text = "Amlodipine 5 mg"
    ent = ExtractedEntities(
        medications=[MedicationEntity(name="Amlodipine", strength="5 mg", frequency="once daily", source_text="Amlodipine 5 mg")]
    )
    create_mock_response(mock_genai_client, ent)
    provider = GeminiExtractionProvider()
    res = provider.extract(ocr_text, 1)
    assert len(res.medications) == 0

def test_invented_lab_value_rejected(mock_env, mock_genai_client):
    ocr_text = "Glucose test done."
    ent = ExtractedEntities(
        lab_results=[LabResult(test_name="Glucose", value="140", source_text="Glucose test done.")]
    )
    create_mock_response(mock_genai_client, ent)
    provider = GeminiExtractionProvider()
    res = provider.extract(ocr_text, 1)
    assert len(res.lab_results) == 0

def test_invented_reference_range_rejected(mock_env, mock_genai_client):
    ocr_text = "Glucose 140 mg/dL"
    ent = ExtractedEntities(
        lab_results=[LabResult(test_name="Glucose", value="140", unit="mg/dL", reference_high="100", source_text="Glucose 140 mg/dL")]
    )
    create_mock_response(mock_genai_client, ent)
    provider = GeminiExtractionProvider()
    res = provider.extract(ocr_text, 1)
    assert len(res.lab_results) == 0

def test_invented_allergy_rejected(mock_env, mock_genai_client):
    ocr_text = "No known allergies"
    ent = ExtractedEntities(
        other=[GenericEntity(value="Allergy: Penicillin", source_text="Allergy: Penicillin")]
    )
    create_mock_response(mock_genai_client, ent)
    provider = GeminiExtractionProvider()
    res = provider.extract(ocr_text, 1)
    assert len(res.other) == 0

def test_invented_procedure_rejected(mock_env, mock_genai_client):
    ocr_text = "Normal checkup"
    ent = ExtractedEntities(
        other=[GenericEntity(value="Procedure: MRI", source_text="Procedure: MRI")]
    )
    create_mock_response(mock_genai_client, ent)
    provider = GeminiExtractionProvider()
    res = provider.extract(ocr_text, 1)
    assert len(res.other) == 0

def test_source_provenance_preserved(mock_env, mock_genai_client):
    ocr_text = "Diagnosis: Hypertension"
    ent = ExtractedEntities(
        diagnoses=[DiagnosisEntity(diagnosis="Hypertension", source_text="Diagnosis: Hypertension")]
    )
    create_mock_response(mock_genai_client, ent)
    provider = GeminiExtractionProvider()
    res = provider.extract(ocr_text, 1)
    assert res.diagnoses[0].source_text == "Diagnosis: Hypertension"
    assert res.diagnoses[0].page_number == 1

def test_confidence_not_fabricated(mock_env, mock_genai_client):
    ocr_text = "Diagnosis: Hypertension"
    ent = ExtractedEntities(
        diagnoses=[DiagnosisEntity(diagnosis="Hypertension", source_text="Hypertension")]
    )
    create_mock_response(mock_genai_client, ent)
    provider = GeminiExtractionProvider()
    res = provider.extract(ocr_text, 1)
    assert res.diagnoses[0].confidence_level == ConfidenceLevel.HIGH

def test_case_normalization_works(mock_env, mock_genai_client):
    ocr_text = "AMLODIPINE 5 MG"
    ent = ExtractedEntities(
        medications=[MedicationEntity(name="Amlodipine", strength="5 mg", source_text="Amlodipine 5 mg")]
    )
    create_mock_response(mock_genai_client, ent)
    provider = GeminiExtractionProvider()
    res = provider.extract(ocr_text, 1)
    assert len(res.medications) == 1

def test_numeric_values_not_fuzzy_matched(mock_env, mock_genai_client):
    ocr_text = "Amlodipine 5 mg"
    ent = ExtractedEntities(
        medications=[MedicationEntity(name="Amlodipine", strength="50 mg", source_text="Amlodipine 50 mg")]
    )
    create_mock_response(mock_genai_client, ent)
    provider = GeminiExtractionProvider()
    res = provider.extract(ocr_text, 1)
    assert len(res.medications) == 0

def test_gemini_api_failure(mock_env, mock_genai_client):
    mock_instance = mock_genai_client.return_value
    mock_instance.models.generate_content.side_effect = Exception("503")
    provider = GeminiExtractionProvider()
    with pytest.raises(RuntimeError, match="Gemini API failure"):
        provider.extract("Hello", 1)

def test_malformed_structured_response(mock_env, mock_genai_client):
    mock_instance = mock_genai_client.return_value
    mock_response = MagicMock()
    mock_response.text = "invalid json"
    mock_instance.models.generate_content.return_value = mock_response
    provider = GeminiExtractionProvider()
    with pytest.raises(ValueError, match="Failed to parse"):
        provider.extract("Hello", 1)

def test_provider_factory_selection(monkeypatch):
    from ai.medical_extraction.service import get_extraction_provider
    monkeypatch.setenv("EXTRACTION_MODE", "real")
    monkeypatch.setenv("GEMINI_API_KEY", "fake")
    provider = get_extraction_provider()
    assert isinstance(provider, GeminiExtractionProvider)
    
    monkeypatch.setenv("EXTRACTION_MODE", "mock")
    provider = get_extraction_provider()
    assert type(provider).__name__ == "MockExtractionProvider"
    
    monkeypatch.setenv("EXTRACTION_MODE", "invalid")
    with pytest.raises(ValueError, match="Unknown EXTRACTION_MODE"):
        get_extraction_provider()
