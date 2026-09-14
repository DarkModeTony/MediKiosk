import pytest
from ai.summarization.mock_provider import MockSummaryProvider
from ai.summarization.models import ClinicalSummaryInput, SourceReference, SourceType

def test_mock_provider_generic_no_hallucination():
    provider = MockSummaryProvider()
    
    # Test strict adherence, sparse input
    input_data = ClinicalSummaryInput(
        medications=["Paracetamol 500 mg"],
        symptoms=[] # No diagnosis
    )
    
    draft = provider.generate(input_data)
    
    # Ensure medication is there
    meds_section = next(s for s in draft.structured_sections if "CURRENT MEDICATIONS" in s.title)
    assert "Paracetamol 500 mg" in meds_section.content
    
    # Ensure diagnosis is "Not documented"
    hx_section = next(s for s in draft.structured_sections if "RELEVANT MEDICAL HISTORY" in s.title)
    assert "Not documented" in hx_section.content or hx_section.content == ""
    
    # Red flags should say None
    rf_section = next(s for s in draft.structured_sections if "RED FLAGS" in s.title)
    assert "None identified" in rf_section.content

def test_mock_provider_scenario_a():
    provider = MockSummaryProvider()
    input_data = ClinicalSummaryInput(
        chief_complaint="chest pain",
        symptoms=["chest pain", "sudden onset"],
        past_medical_history=["Hypertension"],
        medications=["Amlodipine 5 mg once daily"],
        investigations=["Hemoglobin 10.2 g/dL (ABNORMAL)"],
        red_flags=[{"rule_name": "CHEST_PAIN_SUDDEN_ONSET", "severity": "HIGH"}]
    )
    
    draft = provider.generate(input_data)
    
    cc_section = next(s for s in draft.structured_sections if "CHIEF COMPLAINT" in s.title)
    assert "chest pain" in cc_section.content
    
    rf_section = next(s for s in draft.structured_sections if "RED FLAGS" in s.title)
    assert "HIGH" in rf_section.content
    
    lab_section = next(s for s in draft.structured_sections if "INVESTIGATIONS" in s.title)
    assert "Hemoglobin 10.2 g/dL (ABNORMAL)" in lab_section.content
    
    overall = next(s for s in draft.structured_sections if "CLINICAL SUMMARY" in s.title)
    assert "HIGH PRIORITY" in overall.content

def test_mock_provider_sparse_encounter():
    provider = MockSummaryProvider()
    input_data = ClinicalSummaryInput(
        chief_complaint="Headache"
    )
    
    draft = provider.generate(input_data)
    
    cc_section = next(s for s in draft.structured_sections if "CHIEF COMPLAINT" in s.title)
    assert "Headache" in cc_section.content
    
    hx_section = next(s for s in draft.structured_sections if "HISTORY OF PRESENT ILLNESS" in s.title)
    assert hx_section.content == "Not documented"
    
    # Ensure no invented vitals or treatments
    overall = next(s for s in draft.structured_sections if "CLINICAL SUMMARY" in s.title)
    assert "Patient presented with 0 symptoms" in overall.content
