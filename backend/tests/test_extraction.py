import pytest
from ai.medical_extraction.mock_provider import MockExtractionProvider

def test_medication_extraction_no_hallucination():
    provider = MockExtractionProvider()
    text = "Paracetamol 500 mg"
    
    result = provider.extract(text, 1)
    
    assert len(result.medications) == 1
    med = result.medications[0]
    
    # Assert present fields
    assert med.name == "Paracetamol"
    assert med.strength == "500 mg"
    
    # Assert missing fields are None (no hallucination)
    assert med.dosage is None
    assert med.frequency is None
    assert med.route is None
    assert med.duration is None

def test_lab_abnormal_detection():
    provider = MockExtractionProvider()
    
    # Test 1: Explicitly abnormal by range
    text1 = "Haemoglobin: 10.2 g/dL\nReference Range: 12-16 g/dL"
    r1 = provider.extract(text1, 1)
    assert r1.lab_results[0].abnormal_flag is True
    
    # Test 2: Missing reference range
    text2 = "Haemoglobin: 10.2 g/dL"
    r2 = provider.extract(text2, 1)
    assert r2.lab_results[0].abnormal_flag is None # Must not guess!

    # Test 3: Normal lab
    text3 = "WBC: 7,200 /uL\nReference Range: 4,000-11,000 /uL"
    r3 = provider.extract(text3, 1)
    assert r3.lab_results[0].abnormal_flag is False

def test_document_date():
    provider = MockExtractionProvider()
    
    # Date present
    t1 = "Date: 12/08/2026"
    r1 = provider.extract(t1, 1)
    assert r1.document_date == "2026-08-12"
    
    # Date missing
    t2 = "No date here"
    r2 = provider.extract(t2, 1)
    assert r2.document_date is None
