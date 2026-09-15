from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Encounter, RedFlag, Patient, User
from app.api.deps import get_current_user, verify_encounter_access

router = APIRouter()

@router.get("/active")
def get_active_encounters(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Encounter).join(Patient, Encounter.patient_id == Patient.id)
    if current_user.hospital_id:
        query = query.filter(Patient.hospital_id == current_user.hospital_id)
    
    encounters = query.filter(Encounter.status == "IN_PROGRESS").all()
    queue = []
    for enc in encounters:
        patient = db.query(Patient).filter(Patient.id == enc.patient_id).first()
        red_flags = db.query(RedFlag).filter(RedFlag.encounter_id == str(enc.id)).all()
        priority = "NORMAL"
        if any(rf.severity == "HIGH" for rf in red_flags):
            priority = "HIGH"
        elif any(rf.severity == "MEDIUM" for rf in red_flags):
            priority = "MEDIUM"
            
        demo = patient.demographic_data or {} if patient else {}
        
        queue.append({
            "id": str(enc.id),
            "patient_id": str(enc.patient_id),
            "status": enc.status,
            "priority": priority,
            "name": demo.get("name", "Unknown"),
            "age": demo.get("age"),
            "gender": demo.get("gender"),
            "arrival": enc.start_time.isoformat() if enc.start_time else None
        })
    return queue

@router.get("/{encounter_id}")
def get_encounter(
    encounter_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    encounter = verify_encounter_access(encounter_id, current_user, db)
        
    # Get red flags to determine priority
    red_flags = db.query(RedFlag).filter(RedFlag.encounter_id == str(encounter.id)).all()
    priority = "NORMAL"
    if any(rf.severity == "HIGH" for rf in red_flags):
        priority = "HIGH"
    elif any(rf.severity == "MEDIUM" for rf in red_flags):
        priority = "MEDIUM"
        
    return {
        "id": str(encounter.id),
        "patient_id": str(encounter.patient_id),
        "status": encounter.status,
        "priority": priority,
        "chief_complaint": None, # Stored in history, retrieved via /clinical/state
        "start_time": encounter.start_time,
        "end_time": encounter.end_time
    }
