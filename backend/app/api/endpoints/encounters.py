from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Encounter, RedFlag, Patient, User, ClinicalHistory
from app.api.deps import get_current_user, verify_encounter_access, get_or_create_default_hospital

router = APIRouter()

@router.get("/active")
def get_active_encounters(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Encounter).join(Patient, Encounter.patient_id == Patient.id)
    if current_user.hospital_id:
        default_hosp = get_or_create_default_hospital(db)
        if current_user.hospital_id == default_hosp.id:
            query = query.filter(
                (Patient.hospital_id == current_user.hospital_id) | (Patient.hospital_id.is_(None))
            )
        else:
            query = query.filter(Patient.hospital_id == current_user.hospital_id)
    
    encounters = query.filter(
        Encounter.status.in_(["IN_PROGRESS", "WAITING_FOR_DOCTOR", "WAITING", "IN_CONSULTATION"])
    ).order_by(Encounter.start_time.desc()).all()

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
        clin_hist = db.query(ClinicalHistory).filter(ClinicalHistory.encounter_id == enc.id).first()
        chief_complaint = (clin_hist.history_data or {}).get("chief_complaint") if clin_hist else None
        if not chief_complaint:
            chief_complaint = "New Patient Registration / General Intake"
        
        queue.append({
            "id": str(enc.id),
            "patient_id": str(enc.patient_id),
            "status": enc.status,
            "priority": priority,
            "name": demo.get("name", "Unknown"),
            "age": demo.get("age") or demo.get("date_of_birth") or "--",
            "gender": demo.get("gender") or "Unknown",
            "chief_complaint": chief_complaint,
            "red_flag_count": len(red_flags),
            "red_flag_severity": priority if priority != "NORMAL" else None,
            "arrival": enc.start_time.isoformat() if enc.start_time else None,
            "created_at": enc.start_time.isoformat() if enc.start_time else None,
            "updated_at": enc.start_time.isoformat() if enc.start_time else None,
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

@router.get("/{encounter_id}/timeline")
def get_encounter_timeline(
    encounter_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    encounter = verify_encounter_access(encounter_id, current_user, db)
    from app.api.endpoints.documents import get_patient_timeline
    return get_patient_timeline(
        patient_id=str(encounter.patient_id),
        encounter_id=str(encounter.id),
        db=db,
        current_user=current_user
    )
