from typing import List, Optional, Any, Dict
from pydantic import BaseModel
from enum import Enum
from datetime import datetime

class SourceType(str, Enum):
    CLINICAL_INTERVIEW = "CLINICAL_INTERVIEW"
    MEDICAL_DOCUMENT = "MEDICAL_DOCUMENT"
    OCR = "OCR"
    PATIENT_CORRECTION = "PATIENT_CORRECTION"
    OTHER = "OTHER"

class SourceReference(BaseModel):
    source_type: SourceType
    source_id: str
    document_id: Optional[str] = None
    page_number: Optional[int] = None
    source_text: Optional[str] = None
    fact: str
    confidence: Optional[float] = None

class SummaryStatus(str, Enum):
    AI_DRAFT = "AI_DRAFT"
    DOCTOR_EDITED = "DOCTOR_EDITED"
    DOCTOR_VERIFIED = "DOCTOR_VERIFIED"
    REJECTED = "REJECTED"

class ClinicalSummaryInput(BaseModel):
    patient_context: Optional[Dict[str, Any]] = None
    encounter_context: Optional[Dict[str, Any]] = None
    chief_complaint: Optional[str] = None
    history_of_present_illness: Optional[str] = None
    symptoms: List[str] = []
    past_medical_history: List[str] = []
    past_surgical_history: List[str] = []
    medications: List[str] = []
    allergies: List[str] = []
    family_history: List[str] = []
    personal_history: List[str] = []
    review_of_systems: List[str] = []
    ayush_history: List[str] = []
    investigations: List[str] = []
    procedures: List[str] = []
    red_flags: List[Dict[str, Any]] = []
    previous_documents: List[str] = []

class ClinicalSummarySection(BaseModel):
    title: str
    content: str

class ClinicalSummaryDraft(BaseModel):
    id: str
    encounter_id: str
    version: int
    generated_at: datetime
    provider: str
    status: SummaryStatus
    structured_sections: List[ClinicalSummarySection]
    source_references: List[SourceReference]
