from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.models.models import Patient

router = APIRouter()

class PatientRegistrationRequest(BaseModel):
    demographic_data: dict
    consent: bool = True

@router.get("/{patient_id}")
def get_patient(patient_id: str, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
        
    demo = patient.demographic_data or {}
    return {
        "id": str(patient.id),
        "name": demo.get("name", "Unknown"),
        "age": demo.get("age"),
        "gender": demo.get("gender"),
        "created_at": patient.created_at
    }

@router.post("/register")
def register_patient(payload: PatientRegistrationRequest, db: Session = Depends(get_db)):
    # Create the patient
    patient = Patient(demographic_data=payload.demographic_data)
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return {"patient_id": str(patient.id)}
