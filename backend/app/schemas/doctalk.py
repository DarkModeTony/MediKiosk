import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator


VALID_DURATIONS = (3, 5, 7)
VALID_STATUSES = (
    "REQUESTED",
    "ACCEPTED",
    "DECLINED",
    "CANCELLED",
    "EXPIRED",
    "IN_PROGRESS",
    "COMPLETED",
)


class SharingScopePreferences(BaseModel):
    include_history: bool = True
    include_vitals: bool = True
    include_allergies: bool = True
    include_medications: bool = True
    include_conditions: bool = True
    include_investigations: bool = True
    include_documents: bool = True
    include_summary: bool = True
    selected_document_ids: Optional[List[str]] = None
    selected_investigation_ids: Optional[List[str]] = None


class ConsultationCreateRequest(BaseModel):
    encounter_id: str
    specialist_id: Optional[str] = None
    specialty: str
    reason: str
    urgency: str = Field(default="ROUTINE", description="ROUTINE, URGENT, or STAT")
    requested_duration_minutes: int = Field(default=5, description="3, 5, or 7 minutes only")
    access_scope: Optional[Dict[str, Any]] = None
    sharing_preferences: Optional[SharingScopePreferences] = None
    validity_minutes: Optional[int] = Field(default=None, description="Configurable request validity period before expiration")

    @field_validator("requested_duration_minutes")
    @classmethod
    def validate_duration(cls, v: int) -> int:
        if v not in VALID_DURATIONS:
            raise ValueError("Requested duration must be 3, 5, or 7 minutes")
        return v

    @field_validator("urgency")
    @classmethod
    def validate_urgency(cls, v: str) -> str:
        upper = (v or "").upper()
        if upper not in ("ROUTINE", "URGENT", "STAT"):
            return "ROUTINE"
        return upper


class ConsultationDeclineRequest(BaseModel):
    reason: str = Field(..., min_length=1, description="Reason for declining consultation")


class ConsultationNoteCreate(BaseModel):
    clinical_opinion: str = Field(..., min_length=1, description="Specialist's formal clinical assessment")
    recommendations: Optional[Union[List[Dict[str, Any]], Dict[str, Any], str, List[str]]] = None
    further_evaluation: Optional[str] = None
    follow_up: Optional[str] = None


class ConsultationNoteResponse(BaseModel):
    id: str
    consultation_id: str
    encounter_id: Optional[str] = None
    specialist_id: str
    specialist_name: Optional[str] = None
    specialist_hospital_id: str
    specialist_hospital_name: Optional[str] = None
    clinical_opinion: str
    recommendations: Optional[Any] = None
    further_evaluation: Optional[str] = None
    follow_up: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class ConsultationResponse(BaseModel):
    id: str
    requesting_doctor_id: str
    requesting_doctor_name: Optional[str] = None
    requesting_hospital_id: str
    requesting_hospital_name: Optional[str] = None
    specialist_id: Optional[str] = None
    specialist_name: Optional[str] = None
    specialist_hospital_id: Optional[str] = None
    specialist_hospital_name: Optional[str] = None
    patient_id: str
    patient_name: Optional[str] = None
    patient_home_hospital_id: str
    encounter_id: str
    specialty: str
    reason: str
    urgency: str
    requested_duration_minutes: int
    status: str
    access_scope: Optional[Dict[str, Any]] = None
    access_expires_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    decline_reason: Optional[str] = None
    created_at: datetime
    accepted_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    notes: List[ConsultationNoteResponse] = []


class SpecialistDirectoryItem(BaseModel):
    doctor_id: str
    username: str
    display_name: Optional[str] = None
    specialty: Optional[str] = None
    sub_specialty: Optional[str] = None
    qualification: Optional[str] = None
    hospital_id: str
    hospital_name: Optional[str] = None
    hospital_city: Optional[str] = None
    availability_status: str = "ONLINE"
    doctalk_enabled: bool = True
    is_verified: bool = True


class SpecialistFindAnyResponse(BaseModel):
    """Response for the deterministic find-any-available-specialist endpoint."""
    found: bool
    specialist: Optional[SpecialistDirectoryItem] = None
    message: str = ""


class RoomTokenResponse(BaseModel):
    """Secure authorization token and metadata to join a consultation room."""
    room_id: str
    room_token: str
    role: str  # "REQUESTING_DOCTOR" or "SPECIALIST"
    user_id: str
    user_name: Optional[str] = None
    peer_id: Optional[str] = None
    peer_name: Optional[str] = None
    peer_hospital: Optional[str] = None
    duration_minutes: int
    remaining_seconds: int
    status: str
    ws_url: Optional[str] = None

