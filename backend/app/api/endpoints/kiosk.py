from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime, timedelta
from app.database import get_db
from app.models.models import KioskSession, Patient

router = APIRouter()

class SessionCreateRequest(BaseModel):
    patient_id: Optional[str] = None
    language: str

@router.get("/")
def get_kiosk():
    return []

@router.post("/session")
def create_session(payload: SessionCreateRequest, db: Session = Depends(get_db)):
    # Validate patient_id if provided
    if payload.patient_id:
        patient = None
        target_id = payload.patient_id.strip()
        
        # Check alias
        if target_id.lower() in ["patient_001", "pat_raj_123", "9000000001", "raj", "raj kumar"]:
            for p in db.query(Patient).all():
                demo = p.demographic_data or {}
                if str(demo.get("phone")) == "9000000001" or str(demo.get("name", "")).strip().lower() == "raj kumar":
                    patient = p
                    break
        
        # Try as UUID
        if not patient:
            try:
                target_uuid = uuid.UUID(target_id)
                patient = db.query(Patient).filter(Patient.id == target_uuid).first()
            except ValueError:
                pass

        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
            
        payload.patient_id = str(patient.id)
            
    token = str(uuid.uuid4())
    expires = datetime.utcnow() + timedelta(minutes=60)
    
    # Find active encounter for this patient
    from app.models.models import Encounter
    encounter_id = None
    if payload.patient_id:
        try:
            pat_uuid = uuid.UUID(payload.patient_id)
            active_enc = db.query(Encounter).filter(
                Encounter.patient_id == pat_uuid,
                Encounter.status == "WAITING_FOR_DOCTOR"
            ).order_by(Encounter.start_time.desc()).first()
            if active_enc:
                encounter_id = str(active_enc.id)
        except Exception:
            pass
    
    session = KioskSession(
        session_token=token,
        data={"patient_id": payload.patient_id, "language": payload.language, "encounter_id": encounter_id},
        expires_at=expires
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    
    return {
        "session_token": token,
        "expires_at": expires.isoformat(),
        "encounter_id": encounter_id,
        "patient_id": payload.patient_id
    }
