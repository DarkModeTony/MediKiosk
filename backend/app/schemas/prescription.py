from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class PrescriptionItemCreate(BaseModel):
    medicine_id: Optional[int] = None
    medication_name: str
    generic_name: Optional[str] = None
    strength: Optional[str] = None
    dosage_form: Optional[str] = "Tablet"
    dose: Optional[str] = "1 tablet"
    dose_unit: Optional[str] = "tablet"
    route: Optional[str] = "Oral"
    frequency: Optional[str] = "Twice daily"
    timing: Optional[str] = "After food"
    duration_value: Optional[int] = 5
    duration_unit: Optional[str] = "days"
    quantity: Optional[int] = 10
    indication: Optional[str] = None
    instructions: Optional[str] = None
    is_prn: Optional[bool] = False
    min_interval: Optional[str] = None
    max_daily_dose: Optional[str] = None
    item_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class PrescriptionItemResponse(BaseModel):
    id: str
    prescription_id: str
    medicine_id: Optional[int] = None
    medication_name: str
    generic_name: Optional[str] = None
    strength: Optional[str] = None
    dosage_form: Optional[str] = None
    dose: Optional[str] = None
    dose_unit: Optional[str] = None
    route: Optional[str] = None
    frequency: Optional[str] = None
    timing: Optional[str] = None
    duration_value: Optional[int] = None
    duration_unit: Optional[str] = None
    quantity: Optional[int] = None
    indication: Optional[str] = None
    instructions: Optional[str] = None
    is_prn: Optional[bool] = False
    min_interval: Optional[str] = None
    max_daily_dose: Optional[str] = None
    status: Optional[str] = "active"
    item_metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None

class SafetyAlert(BaseModel):
    type: str # ALLERGY_CONFLICT, DUPLICATE_MEDICATION, CONDITION_CONFLICT, INFO
    severity: str # INFO, CAUTION, HIGH
    title: str
    message: str
    medication_name: str
    source: str # e.g. "Patient Recorded Allergy: Penicillin"

class SafetyCheckResult(BaseModel):
    alerts: List[SafetyAlert] = Field(default_factory=list)
    allergies_reviewed: bool = True
    current_meds_reviewed: bool = True
    patient_history_reviewed: bool = True
    passed_critical: bool = True

class PrescriptionCreateOrUpdate(BaseModel):
    patient_id: Optional[str] = None
    doctor_id: Optional[str] = None
    notes: Optional[str] = None
    items: List[PrescriptionItemCreate] = Field(default_factory=list)

class FinalizePrescriptionRequest(BaseModel):
    doctor_id: Optional[str] = None
    notes: Optional[str] = None
    acknowledged_safety_alerts: Optional[bool] = False

class PrescriptionResponse(BaseModel):
    id: str
    patient_id: Optional[str] = None
    encounter_id: str
    doctor_id: Optional[str] = None
    status: str
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    finalized_at: Optional[datetime] = None
    items: List[PrescriptionItemResponse] = Field(default_factory=list)
    safety_check: Optional[SafetyCheckResult] = None
