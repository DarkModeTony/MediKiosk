import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models.models import Patient, User, Hospital
from app.api.deps import get_current_user, verify_patient_access, get_or_create_default_hospital

router = APIRouter()

class PatientRegistrationRequest(BaseModel):
    demographic_data: dict
    consent: bool = True
    hospital_id: Optional[str] = None

@router.get("/search")
def search_patient(
    q: str,
    db: Session = Depends(get_db)
):
    query_str = (q or "").strip()
    if not query_str:
        raise HTTPException(status_code=400, detail="Search query is required")

    # 1. Check if demo alias for Raj Kumar
    is_raj_alias = query_str.lower() in [
        "patient_001", "pat_raj_123", "raj", "raj kumar", "9000000001"
    ]
    
    patient = None
    if is_raj_alias:
        for p in db.query(Patient).all():
            demo = p.demographic_data or {}
            if str(demo.get("phone")) == "9000000001" or str(demo.get("name", "")).strip().lower() == "raj kumar":
                patient = p
                break

    # 2. Check by UUID directly
    if not patient:
        try:
            target_uuid = uuid.UUID(query_str)
            patient = db.query(Patient).filter(Patient.id == target_uuid).first()
        except ValueError:
            pass

    # 3. Check by phone number or name in demographic_data
    if not patient:
        for p in db.query(Patient).all():
            demo = p.demographic_data or {}
            phone = str(demo.get("phone", "") or demo.get("mobile_number", "") or demo.get("mobile", ""))
            name = str(demo.get("name", "")).lower()
            if query_str in phone or query_str.lower() in name:
                patient = p
                break

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    demo = patient.demographic_data or {}
    return {
        "patient_id": str(patient.id),
        "name": demo.get("name", "Unknown"),
        "age": demo.get("age"),
        "gender": demo.get("gender"),
        "phone": demo.get("phone", demo.get("mobile_number")),
        "hospital_id": str(patient.hospital_id) if patient.hospital_id else None
    }

@router.get("/{patient_id}")
def get_patient(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    patient = verify_patient_access(patient_id, current_user, db)
        
    demo = patient.demographic_data or {}
    return {
        "id": str(patient.id),
        "name": demo.get("name", "Unknown"),
        "age": demo.get("age"),
        "gender": demo.get("gender"),
        "hospital_id": str(patient.hospital_id) if patient.hospital_id else None,
        "created_at": patient.created_at
    }

@router.post("/register")
def register_patient(
    payload: PatientRegistrationRequest,
    x_hospital_id: Optional[str] = Header(None),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    # Determine hospital for patient registration
    hospital_id = None
    target_hosp_id = payload.hospital_id or x_hospital_id
    if target_hosp_id:
        try:
            hosp_uuid = uuid.UUID(target_hosp_id)
            hosp = db.query(Hospital).filter(Hospital.id == hosp_uuid).first()
            if hosp:
                hospital_id = hosp.id
        except ValueError:
            pass
            
    if not hospital_id and current_user and current_user.hospital_id:
        hospital_id = current_user.hospital_id

    if not hospital_id:
        default_hosp = get_or_create_default_hospital(db)
        hospital_id = default_hosp.id

    patient = Patient(
        hospital_id=hospital_id,
        demographic_data=payload.demographic_data
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return {
        "patient_id": str(patient.id),
        "hospital_id": str(patient.hospital_id) if patient.hospital_id else None
    }
