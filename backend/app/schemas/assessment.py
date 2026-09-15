from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class VitalsExam(BaseModel):
    bp_systolic: Optional[int] = None
    bp_diastolic: Optional[int] = None
    pulse: Optional[int] = None
    temperature: Optional[float] = None
    spo2: Optional[int] = None
    respiratory_rate: Optional[int] = None
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    general_exam: Optional[str] = None
    systemic_exam: Optional[Dict[str, str]] = None # {"cvs": "...", "rs": "...", "pa": "...", "cns": "..."}

class DiagnosisItem(BaseModel):
    condition: str
    type: str = "PROVISIONAL" # PROVISIONAL, CONFIRMED, DIFFERENTIAL
    icd10: Optional[str] = None
    notes: Optional[str] = None

class ConfirmedAllergyItem(BaseModel):
    allergen: str
    reaction: Optional[str] = None
    severity: Optional[str] = "MILD" # MILD, MODERATE, SEVERE, LIFE_THREATENING

class AssessmentSaveRequest(BaseModel):
    hpi: Optional[str] = None
    vitals_examination: Optional[Dict[str, Any]] = None
    allergies_confirmed: Optional[List[Dict[str, Any]]] = None
    medications_confirmed: Optional[List[Dict[str, Any]]] = None
    diagnosis: Optional[List[Dict[str, Any]]] = None
    clinical_plan: Optional[str] = None

class AssessmentFinalizeRequest(BaseModel):
    notes: Optional[str] = None

class AssessmentResponse(BaseModel):
    id: str
    encounter_id: str
    patient_id: Optional[str]
    doctor_id: Optional[str]
    hpi: Optional[str]
    vitals_examination: Optional[Dict[str, Any]]
    allergies_confirmed: Optional[List[Dict[str, Any]]]
    medications_confirmed: Optional[List[Dict[str, Any]]]
    diagnosis: Optional[List[Dict[str, Any]]]
    clinical_plan: Optional[str]
    status: str
    finalized_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
