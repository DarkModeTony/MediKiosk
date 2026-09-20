import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel

from datetime import datetime
from app.database import get_db
from app.models.models import Patient, User, Hospital, Encounter, PatientLongitudinalProfile
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

    DEMO_PATIENT_MAP = {
        "patient_001": "9000000001", "pat_raj_123": "9000000001", "raj": "9000000001", "raj kumar": "9000000001", "9000000001": "9000000001",
        "patient_002": "9000000002", "anita": "9000000002", "anita desai": "9000000002", "9000000002": "9000000002",
        "patient_003": "9000000003", "mohan": "9000000003", "mohan lal verma": "9000000003", "9000000003": "9000000003",
        "patient_004": "9000000004", "priya": "9000000004", "priya swaminathan": "9000000004", "9000000004": "9000000004",
        "patient_005": "9000000005", "arjun": "9000000005", "arjun patel": "9000000005", "9000000005": "9000000005",
        "patient_006": "9000000006", "sunita": "9000000006", "sunita roy": "9000000006", "9000000006": "9000000006",
        "patient_007": "9000000007", "harpreet": "9000000007", "harpreet singh": "9000000007", "9000000007": "9000000007",
    }
    
    patient = None
    target_phone = DEMO_PATIENT_MAP.get(query_str.lower())
    if target_phone:
        for p in db.query(Patient).all():
            demo = p.demographic_data or {}
            if str(demo.get("phone")) == target_phone:
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

    # 1. Create fresh, isolated encounter strictly for this new patient
    encounter = Encounter(
        patient_id=patient.id,
        status="IN_PROGRESS",
        start_time=datetime.utcnow()
    )
    db.add(encounter)
    db.commit()
    db.refresh(encounter)

    # 2. Create clean, empty longitudinal profile (no inherited history)
    empty_profile = {
        "schema_version": "1.0",
        "last_updated": datetime.utcnow().isoformat(),
        "medical_history": {
            "chronic_conditions": [],
            "surgeries": [],
            "hospitalizations": []
        },
        "allergies": {
            "known": []
        },
        "current_medications": [],
        "family_history": {},
        "social_history": {},
        "vitals_last": {}
    }
    long_profile = PatientLongitudinalProfile(
        patient_id=patient.id,
        schema_version="1.0",
        profile=empty_profile
    )
    db.add(long_profile)
    db.commit()

    return {
        "patient_id": str(patient.id),
        "encounter_id": str(encounter.id),
        "hospital_id": str(patient.hospital_id) if patient.hospital_id else None
    }
