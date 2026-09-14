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
        patient = db.query(Patient).filter(Patient.id == payload.patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
            
    token = str(uuid.uuid4())
    expires = datetime.utcnow() + timedelta(minutes=60)
    
    session = KioskSession(
        session_token=token,
        data={"patient_id": payload.patient_id, "language": payload.language},
        expires_at=expires
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    
    return {
        "session_token": token,
        "expires_at": expires.isoformat()
    }
