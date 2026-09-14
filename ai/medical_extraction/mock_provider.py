from typing import List
from .interface import ExtractionProvider
from .models import (
    ExtractedEntities, MedicationEntity, LabResult, 
    DiagnosisEntity, ConfidenceLevel, GenericEntity
)

class MockExtractionProvider(ExtractionProvider):
    def extract(self, text: str, page_number: int) -> ExtractedEntities:
        entities = ExtractedEntities()
        
        # Safe string handling
        t = text.lower()
        
        # Rule 1: Medical Prescription parsing (Mock deterministic)
        if "amlodipine 5 mg once daily" in t:
            entities.medications.append(
                MedicationEntity(
                    source_text="Amlodipine 5 mg once daily",
                    page_number=page_number,
                    confidence_level=ConfidenceLevel.HIGH,
                    name="Amlodipine",
                    strength="5 mg",
                    frequency="once daily",
                    dosage=None,
                    route=None,
                    duration=None
                )
            )
        elif "paracetamol 500 mg" in t:
            entities.medications.append(
                MedicationEntity(
                    source_text="Paracetamol 500 mg",
                    page_number=page_number,
                    confidence_level=ConfidenceLevel.HIGH,
                    name="Paracetamol",
                    strength="500 mg",
                    dosage=None,
                    frequency=None,
                    route=None,
                    duration=None
                )
            )
            
        if "hypertension" in t:
            entities.diagnoses.append(
                DiagnosisEntity(
                    source_text="Hypertension",
                    page_number=page_number,
                    confidence_level=ConfidenceLevel.HIGH,
                    diagnosis="Hypertension"
                )
            )
            
        if "patient: raj kumar" in t:
            entities.patient_info.append(
                GenericEntity(source_text="Patient: Raj Kumar", value="Name: Raj Kumar", page_number=page_number)
            )
            
        if "12/08/2026" in text:
            entities.document_date = "2026-08-12"

        # Rule 2: Lab Results parsing (Mock deterministic)
        if "haemoglobin: 10.2" in t:
            if "reference range" in t:
                # Deterministic extraction based on expected mock text
                entities.lab_results.append(
                    LabResult(
                        source_text="Haemoglobin: 10.2 g/dL\nReference Range: 12-16 g/dL",
                        page_number=page_number,
                        confidence_level=ConfidenceLevel.HIGH,
                        test_name="Hemoglobin",
                        value="10.2",
                        unit="g/dL",
                        reference_low="12",
                        reference_high="16",
                        abnormal_flag=True # Evaluated as 10.2 < 12 safely
                    )
                )
            else:
                # Missing reference range case
                entities.lab_results.append(
                    LabResult(
                        source_text="Haemoglobin: 10.2 g/dL",
                        page_number=page_number,
                        confidence_level=ConfidenceLevel.HIGH,
                        test_name="Hemoglobin",
                        value="10.2",
                        unit="g/dL",
                        reference_low=None,
                        reference_high=None,
                        abnormal_flag=None # MUST BE NULL
                    )
                )
            
        if "wbc: 7,200" in t:
            entities.lab_results.append(
                LabResult(
                    source_text="WBC: 7,200 /uL\nReference Range: 4,000-11,000 /uL",
                    page_number=page_number,
                    confidence_level=ConfidenceLevel.HIGH,
                    test_name="WBC",
                    value="7,200",
                    unit="/uL",
                    reference_low="4,000",
                    reference_high="11,000",
                    abnormal_flag=False # Normal
                )
            )

        return entities
