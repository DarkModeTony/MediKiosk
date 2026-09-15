from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class InvestigationResultCreate(BaseModel):
    parameter_name: str
    value: str
    unit: Optional[str] = None
    reference_range: Optional[str] = None
    abnormal_flag: Optional[str] = "NORMAL" # NORMAL, LOW, HIGH, CRITICAL, ABNORMAL
    result_notes: Optional[str] = None

class InvestigationResultResponse(BaseModel):
    id: str
    order_id: str
    parameter_name: str
    value: str
    unit: Optional[str]
    reference_range: Optional[str]
    abnormal_flag: str
    result_notes: Optional[str]
    created_at: datetime

class InvestigationOrderCreate(BaseModel):
    test_name: str
    test_type: str = "LAB" # LAB, RADIOLOGY, PATHOLOGY, CARDIOLOGY, OTHER
    urgency: str = "ROUTINE" # ROUTINE, URGENT, STAT
    clinical_notes: Optional[str] = None

class InvestigationOrderResponse(BaseModel):
    id: str
    encounter_id: str
    patient_id: str
    doctor_id: Optional[str]
    test_name: str
    test_type: str
    urgency: str
    clinical_notes: Optional[str]
    status: str # ORDERED, PENDING, COMPLETED, REVIEWED, CANCELLED
    ordered_at: datetime
    completed_at: Optional[datetime]
    reviewed_at: Optional[datetime]
    reviewed_by: Optional[str]
    results: List[InvestigationResultResponse] = []
    created_at: datetime
    updated_at: datetime

class AddResultsRequest(BaseModel):
    results: List[InvestigationResultCreate]

class ReviewOrderRequest(BaseModel):
    notes: Optional[str] = None
