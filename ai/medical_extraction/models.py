from typing import Optional
from enum import Enum
from pydantic import BaseModel

class EntityType(str, Enum):
    PATIENT_INFO = "PATIENT_INFO"
    DIAGNOSIS = "DIAGNOSIS"
    MEDICATION = "MEDICATION"
    ALLERGY = "ALLERGY"
    LAB_RESULT = "LAB_RESULT"
    PROCEDURE = "PROCEDURE"
    SYMPTOM = "SYMPTOM"
    CLINICAL_FINDING = "CLINICAL_FINDING"
    OTHER = "OTHER"

class VerificationStatus(str, Enum):
    AI_EXTRACTED = "AI_EXTRACTED"
    PATIENT_CORRECTED = "PATIENT_CORRECTED"
    DOCTOR_VERIFIED = "DOCTOR_VERIFIED"
    REJECTED = "REJECTED"

class ConfidenceLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class BaseEntity(BaseModel):
    source_text: str
    page_number: Optional[int] = None
    confidence_level: ConfidenceLevel = ConfidenceLevel.HIGH

class MedicationEntity(BaseEntity):
    name: Optional[str] = None
    strength: Optional[str] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    route: Optional[str] = None
    duration: Optional[str] = None

class LabResult(BaseEntity):
    test_name: Optional[str] = None
    value: Optional[str] = None
    unit: Optional[str] = None
    reference_low: Optional[str] = None
    reference_high: Optional[str] = None
    interpretation: Optional[str] = None
    abnormal_flag: Optional[bool] = None

class DiagnosisEntity(BaseEntity):
    diagnosis: Optional[str] = None
    normalized_value: Optional[str] = None

class GenericEntity(BaseEntity):
    value: str

class ExtractedEntities(BaseModel):
    medications: list[MedicationEntity] = []
    lab_results: list[LabResult] = []
    diagnoses: list[DiagnosisEntity] = []
    patient_info: list[GenericEntity] = []
    other: list[GenericEntity] = []
    document_date: Optional[str] = None
