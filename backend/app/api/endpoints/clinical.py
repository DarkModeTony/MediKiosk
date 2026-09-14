import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models.models import Encounter, ClinicalHistory, Symptom, RedFlag as DBRedFlag, KioskSession
from ai.question_engine.engine import QuestionEngine
from ai.question_engine.models import ClinicalState, Answer, Question
from ai.question_engine.pathways import get_pathway
from ai.red_flags.engine import RedFlagEngine
from ai.clinical_nlu.service import ClinicalNLUService

router = APIRouter()

# Instantiate services (in a real app, use dependency injection)
red_flag_engine = RedFlagEngine()
nlu_service = ClinicalNLUService()
question_engine = QuestionEngine(red_flag_engine, nlu_service)

def get_or_create_history(db: Session, encounter_id: str) -> ClinicalHistory:
    history = db.query(ClinicalHistory).filter(ClinicalHistory.encounter_id == encounter_id).first()
    if not history:
        history = ClinicalHistory(encounter_id=encounter_id, history_data={})
        db.add(history)
        db.commit()
        db.refresh(history)
    return history

@router.post("/start", response_model=ClinicalState)
def start_clinical_intake(session_token: str, db: Session = Depends(get_db)):
    # Verify session
    kiosk_session = db.query(KioskSession).filter(KioskSession.session_token == session_token).first()
    if not kiosk_session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Check if encounter exists in session, else create one
    encounter_id = kiosk_session.data.get("encounter_id")
    if not encounter_id:
        patient_id = kiosk_session.data.get("patient_id")
        encounter = Encounter(patient_id=patient_id, status="IN_PROGRESS")
        db.add(encounter)
        db.commit()
        db.refresh(encounter)
        encounter_id = str(encounter.id)
        
        # Update session
        kiosk_session.data = {**kiosk_session.data, "encounter_id": encounter_id}
        db.commit()
        
    state = question_engine.start_interview(encounter_id)
    
    # Save state to history
    history = get_or_create_history(db, encounter_id)
    history.history_data = state.model_dump()
    db.commit()
    
    return state

@router.get("/state", response_model=ClinicalState)
def get_clinical_state(session_token: str, db: Session = Depends(get_db)):
    kiosk_session = db.query(KioskSession).filter(KioskSession.session_token == session_token).first()
    if not kiosk_session or not kiosk_session.data.get("encounter_id"):
        raise HTTPException(status_code=404, detail="Session or encounter not found")
        
    encounter_id = kiosk_session.data.get("encounter_id")
    history = db.query(ClinicalHistory).filter(ClinicalHistory.encounter_id == encounter_id).first()
    
    if not history or not history.history_data:
        # Fallback to start
        return start_clinical_intake(session_token, db)
        
    return ClinicalState(**history.history_data)

@router.post("/answer", response_model=ClinicalState)
def submit_answer(session_token: str, answer: Answer, db: Session = Depends(get_db)):
    # Retrieve current state
    kiosk_session = db.query(KioskSession).filter(KioskSession.session_token == session_token).first()
    if not kiosk_session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    encounter_id = kiosk_session.data.get("encounter_id")
    history = db.query(ClinicalHistory).filter(ClinicalHistory.encounter_id == encounter_id).first()
    if not history or not history.history_data:
        raise HTTPException(status_code=400, detail="Clinical state not initialized")
        
    current_state = ClinicalState(**history.history_data)
    
    # Process answer via engine
    updated_state = question_engine.process_answer(current_state, answer)
    
    # Persist Red Flags to DB if any
    if hasattr(updated_state, "new_red_flags") and updated_state.new_red_flags:
        for rf in updated_state.new_red_flags:
            db_rf = DBRedFlag(
                encounter_id=encounter_id,
                rule_name=rf.rule_name,
                input_evidence=rf.evidence,
                severity=rf.severity,
                status=rf.status
            )
            db.add(db_rf)
        # Clear them so they aren't processed again next time
        updated_state.new_red_flags = []
    
    # Persist structured symptoms (example mapping of facts to symptoms)
    for field, fact in updated_state.facts.items():
        if fact.state == "COLLECTED":
            # Very simplistic mapping: Just dump to symptoms table for audit
            symp = Symptom(
                encounter_id=encounter_id,
                symptom_name=field,
                details={"value": fact.value, "source": "kiosk_intake"}
            )
            db.add(symp)
            
    # Update state in history
    history.history_data = updated_state.model_dump()
    db.commit()
    
    return updated_state

@router.get("/question/{pathway_name}/{question_id}")
def get_question_details(pathway_name: str, question_id: str):
    pathway = get_pathway(pathway_name)
    if not pathway:
        raise HTTPException(status_code=404, detail="Pathway not found")
    for q in pathway:
        if q.id == question_id:
            return q
    raise HTTPException(status_code=404, detail="Question not found")
