from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import uuid
from datetime import datetime, timedelta

from app.database import get_db
from app.models.models import (
    KioskSession, Patient, Encounter, ClinicalHistory,
    ClinicalSummary, SummaryVerification,
    PatientLongitudinalProfile, PatientFact,
    Prescription, PrescriptionItem, Document
)

router = APIRouter()

DEMO_PATIENT_MAP = {
    "patient_001": "9000000001", "pat_raj_123": "9000000001", "raj": "9000000001", "raj kumar": "9000000001", "9000000001": "9000000001",
    "patient_002": "9000000002", "anita": "9000000002", "anita desai": "9000000002", "9000000002": "9000000002",
    "patient_003": "9000000003", "mohan": "9000000003", "mohan lal verma": "9000000003", "9000000003": "9000000003",
    "patient_004": "9000000004", "priya": "9000000004", "priya swaminathan": "9000000004", "9000000004": "9000000004",
    "patient_005": "9000000005", "arjun": "9000000005", "arjun patel": "9000000005", "9000000005": "9000000005",
    "patient_006": "9000000006", "sunita": "9000000006", "sunita roy": "9000000006", "9000000006": "9000000006",
    "patient_007": "9000000007", "harpreet": "9000000007", "harpreet singh": "9000000007", "9000000007": "9000000007",
}

class SessionCreateRequest(BaseModel):
    patient_id: Optional[str] = None
    language: str

class ProfileUpdateRequest(BaseModel):
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[Dict[str, Any]] = None
    preferred_language: Optional[str] = None
    communication_mode: Optional[str] = None

class MedicalChangeReportRequest(BaseModel):
    category: str  # "allergy", "condition", "medication", "procedure", "general"
    description: str
    details: Optional[Dict[str, Any]] = None

def get_kiosk_session_and_patient(
    x_session_token: Optional[str] = Header(None, alias="X-Session-Token"),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Dependency to authenticate kiosk requests strictly using the active session token.
    Prevents patients from accessing unauthorized patient profiles.
    """
    token = x_session_token
    if not token and authorization:
        if authorization.lower().startswith("bearer "):
            token = authorization[7:].strip()
        else:
            token = authorization.strip()

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Session authentication required. Missing X-Session-Token header."
        )

    session = db.query(KioskSession).filter(KioskSession.session_token == token).first()
    if not session:
        raise HTTPException(status_code=401, detail="Invalid kiosk session token.")

    if session.expires_at and session.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Kiosk session has expired. Please log in again.")

    session_data = session.data or {}
    patient_id = session_data.get("patient_id")
    if not patient_id:
        raise HTTPException(status_code=403, detail="No patient associated with this active session.")

    try:
        pat_uuid = uuid.UUID(patient_id)
        patient = db.query(Patient).filter(Patient.id == pat_uuid).first()
    except ValueError:
        patient = None

    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found.")

    return session, patient

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
        target_phone = DEMO_PATIENT_MAP.get(target_id.lower())
        if target_phone:
            for p in db.query(Patient).all():
                demo = p.demographic_data or {}
                if str(demo.get("phone")) == target_phone:
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
    
    # Find or create active encounter strictly for THIS patient
    encounter_id = None
    if payload.patient_id:
        try:
            pat_uuid = uuid.UUID(payload.patient_id)
            active_enc = db.query(Encounter).filter(
                Encounter.patient_id == pat_uuid,
                Encounter.status.in_(["IN_PROGRESS", "WAITING_FOR_DOCTOR"])
            ).order_by(Encounter.start_time.desc()).first()
            if not active_enc:
                active_enc = Encounter(
                    patient_id=pat_uuid,
                    status="IN_PROGRESS",
                    start_time=datetime.utcnow()
                )
                db.add(active_enc)
                db.commit()
                db.refresh(active_enc)
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

@router.get("/profile")
def get_patient_profile(
    auth_data = Depends(get_kiosk_session_and_patient),
    db: Session = Depends(get_db)
):
    """
    Returns the comprehensive profile for the authenticated kiosk patient:
    - Personal demographics
    - Medical profile summary (conditions, allergies, current medications, surgeries)
    - Recent hospital activity & visit notes
    - Active prescriptions
    """
    session, patient = auth_data
    demo = patient.demographic_data or {}

    # 1. Fetch Longitudinal Profile
    long_prof = db.query(PatientLongitudinalProfile).filter(
        PatientLongitudinalProfile.patient_id == patient.id
    ).first()
    prof_data = long_prof.profile if long_prof else {}

    # 2. Encounters & Doctor Notes
    encounters = db.query(Encounter).filter(
        Encounter.patient_id == patient.id
    ).order_by(Encounter.start_time.desc()).limit(8).all()

    recent_activity = []
    for enc in encounters:
        summary = db.query(ClinicalSummary).filter(ClinicalSummary.encounter_id == enc.id).first()
        doc_note = None
        if summary and summary.verifications:
            doc_note = summary.verifications[-1].final_content
        elif summary:
            doc_note = summary.draft_content

        # Get complaints from clinical history if available
        clin_hist = db.query(ClinicalHistory).filter(ClinicalHistory.encounter_id == enc.id).first()
        chief_complaint = (clin_hist.history_data or {}).get("chief_complaint") if clin_hist else None

        recent_activity.append({
            "encounter_id": str(enc.id),
            "date": enc.start_time.isoformat() if enc.start_time else None,
            "status": enc.status,
            "chief_complaint": chief_complaint,
            "doctor_note": doc_note,
        })

    # 3. Prescriptions
    prescriptions = db.query(Prescription).filter(
        Prescription.patient_id == patient.id
    ).order_by(Prescription.created_at.desc()).all()

    rx_list = []
    for rx in prescriptions:
        rx_list.append({
            "id": str(rx.id),
            "status": rx.status,
            "notes": rx.notes,
            "created_at": rx.created_at.isoformat() if rx.created_at else None,
            "finalized_at": rx.finalized_at.isoformat() if rx.finalized_at else None,
            "items": [
                {
                    "name": item.medication_name,
                    "dose": item.dose,
                    "frequency": item.frequency,
                    "instructions": item.instructions,
                    "status": item.status,
                }
                for item in rx.items
            ]
        })

    # 4. Uploaded Documents count
    doc_count = db.query(Document).filter(
        Document.encounter_id.in_([e.id for e in encounters])
    ).count() if encounters else 0

    return {
        "patient_id": str(patient.id),
        "demographics": {
            "name": demo.get("name", "Unknown"),
            "age": demo.get("age"),
            "gender": demo.get("gender"),
            "dob": demo.get("dob"),
            "phone": demo.get("phone", demo.get("mobile_number")),
            "email": demo.get("email"),
            "address": demo.get("address"),
            "city": demo.get("city"),
            "blood_group": demo.get("blood_group"),
            "emergency_contact": demo.get("emergency_contact"),
            "preferred_language": demo.get("preferred_language", "English"),
            "communication_mode": demo.get("communication_mode", "Voice"),
        },
        "profile_summary": {
            "chronic_conditions": prof_data.get("medical_history", {}).get("chronic_conditions", []),
            "allergies": prof_data.get("allergies", {}).get("known", []),
            "current_medications": prof_data.get("current_medications", []),
            "surgeries": prof_data.get("medical_history", {}).get("surgeries", []),
            "hospitalizations": prof_data.get("medical_history", {}).get("hospitalizations", []),
            "vitals_last": prof_data.get("vitals_last", {}),
        },
        "recent_activity": recent_activity,
        "prescriptions": rx_list,
        "documents_count": doc_count,
    }

@router.put("/profile")
def update_patient_profile(
    payload: ProfileUpdateRequest,
    auth_data = Depends(get_kiosk_session_and_patient),
    db: Session = Depends(get_db)
):
    """
    Safely updates patient-editable contact and demographic information.
    Medical facts are protected from direct overwrites.
    """
    session, patient = auth_data
    demo = dict(patient.demographic_data or {})

    if payload.phone is not None and payload.phone.strip():
        demo["phone"] = payload.phone.strip()
    if payload.email is not None:
        demo["email"] = payload.email.strip()
    if payload.address is not None:
        demo["address"] = payload.address.strip()
    if payload.emergency_contact is not None:
        demo["emergency_contact"] = payload.emergency_contact
    if payload.preferred_language is not None:
        demo["preferred_language"] = payload.preferred_language
    if payload.communication_mode is not None:
        demo["communication_mode"] = payload.communication_mode

    patient.demographic_data = demo
    flag_modified(patient, "demographic_data")
    db.commit()
    db.refresh(patient)

    return {
        "status": "success",
        "message": "Profile contact details updated successfully.",
        "demographics": patient.demographic_data
    }

@router.post("/profile/report-change")
def report_medical_change(
    payload: MedicalChangeReportRequest,
    auth_data = Depends(get_kiosk_session_and_patient),
    db: Session = Depends(get_db)
):
    """
    Patient-reported discrepancy in their medical history.
    Appends an unverified fact with 'pending_doctor_review' status into patient_facts.
    Guarantees clinical safety: doctor must review and verify during encounter.
    """
    session, patient = auth_data

    if not payload.description or not payload.description.strip():
        raise HTTPException(status_code=400, detail="Description of the change is required.")

    fact = PatientFact(
        patient_id=patient.id,
        category=payload.category,
        fact_type="patient_reported_discrepancy",
        value={
            "description": payload.description.strip(),
            "details": payload.details or {},
            "status": "pending_doctor_review",
            "reported_at": datetime.utcnow().isoformat()
        },
        source_type="PATIENT_REPORTED",
        confidence=1.0,
        verified=False,
        valid_from=datetime.utcnow()
    )
    db.add(fact)
    db.commit()
    db.refresh(fact)

    return {
        "status": "submitted_for_review",
        "fact_id": str(fact.id),
        "message": "Your reported change has been recorded and flagged for your doctor's clinical review."
    }

@router.get("/medical-history")
def get_patient_medical_history(
    auth_data = Depends(get_kiosk_session_and_patient),
    db: Session = Depends(get_db)
):
    """
    Returns full longitudinal clinical history with categorized domains:
    - Diagnoses / Chronic conditions
    - Medications
    - Allergies (with allergen, reaction, severity, confirmed status)
    - Surgeries & Procedures
    - Family History & Lifestyle / Social History
    - Past Prescriptions
    - Pending Patient-Reported Updates
    """
    session, patient = auth_data

    long_prof = db.query(PatientLongitudinalProfile).filter(
        PatientLongitudinalProfile.patient_id == patient.id
    ).first()
    prof = long_prof.profile if long_prof else {}

    # Patient facts for badges and pending updates
    facts = db.query(PatientFact).filter(
        PatientFact.patient_id == patient.id
    ).order_by(PatientFact.valid_from.desc()).all()

    pending_reports = [
        {
            "id": str(f.id),
            "category": f.category,
            "description": (f.value or {}).get("description", ""),
            "reported_at": (f.value or {}).get("reported_at", f.valid_from.isoformat() if f.valid_from else None),
            "status": "pending_doctor_review"
        }
        for f in facts if not f.verified and f.source_type == "PATIENT_REPORTED"
    ]

    # Prescriptions
    prescriptions = db.query(Prescription).filter(
        Prescription.patient_id == patient.id
    ).order_by(Prescription.created_at.desc()).all()

    return {
        "patient_id": str(patient.id),
        "patient_name": (patient.demographic_data or {}).get("name", "Unknown"),
        "medical_history": prof.get("medical_history", {}),
        "allergies": prof.get("allergies", {}),
        "current_medications": prof.get("current_medications", []),
        "family_history": prof.get("family_history", {}),
        "social_history": prof.get("social_history", {}),
        "vitals_last": prof.get("vitals_last", {}),
        "prescriptions": [
            {
                "id": str(p.id),
                "status": p.status,
                "notes": p.notes,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "finalized_at": p.finalized_at.isoformat() if p.finalized_at else None,
                "items": [
                    {
                        "medication_name": item.medication_name,
                        "dose": item.dose,
                        "frequency": item.frequency,
                        "instructions": item.instructions,
                        "status": item.status
                    }
                    for item in p.items
                ]
            }
            for p in prescriptions
        ],
        "pending_reports": pending_reports
    }

@router.get("/summary")
def get_kiosk_summary(
    auth_data = Depends(get_kiosk_session_and_patient),
    db: Session = Depends(get_db)
):
    """
    Returns the AI summary draft strictly for the authenticated kiosk patient's active encounter.
    Eliminates cross-patient summary leakage by deriving encounter from the validated session.
    """
    session, patient = auth_data
    encounter_id = (session.data or {}).get("encounter_id")
    
    encounter = None
    if encounter_id:
        try:
            enc_uuid = uuid.UUID(encounter_id)
            encounter = db.query(Encounter).filter(
                Encounter.id == enc_uuid,
                Encounter.patient_id == patient.id
            ).first()
        except ValueError:
            pass

    if not encounter:
        # Fallback to the patient's own active encounter
        encounter = db.query(Encounter).filter(
            Encounter.patient_id == patient.id,
            Encounter.status.in_(["IN_PROGRESS", "WAITING_FOR_DOCTOR", "COMPLETED"])
        ).order_by(Encounter.start_time.desc()).first()

    if not encounter:
        raise HTTPException(status_code=404, detail="No encounter found for this session")

    summary = db.query(ClinicalSummary).filter(ClinicalSummary.encounter_id == encounter.id).first()
    if not summary:
        # Generate summary on demand for THIS encounter only
        from ai.summarization.aggregator import ClinicalDataAggregator
        from ai.summarization.service import get_summary_provider

        provider = get_summary_provider()
        aggregator = ClinicalDataAggregator(db)
        input_data, source_refs = aggregator.gather_data(str(encounter.id))
        draft = provider.generate(input_data)
        draft.encounter_id = str(encounter.id)
        draft.source_references = source_refs

        summary = ClinicalSummary(
            encounter_id=encounter.id,
            draft_content=draft.model_dump(mode="json"),
            model_info={"provider": draft.provider, "version": draft.version}
        )
        db.add(summary)
        db.commit()
        db.refresh(summary)

    latest_v = db.query(SummaryVerification).filter(
        SummaryVerification.summary_id == summary.id
    ).order_by(SummaryVerification.verified_at.desc()).first()

    return {
        "summary_id": str(summary.id),
        "encounter_id": str(encounter.id),
        "patient_id": str(patient.id),
        "latest_version": latest_v.final_content if latest_v else summary.draft_content,
        "status": latest_v.status if latest_v else "AI_DRAFT",
        "original_draft": summary.draft_content
    }

@router.post("/summary/generate")
def generate_kiosk_summary(
    auth_data = Depends(get_kiosk_session_and_patient),
    db: Session = Depends(get_db)
):
    """
    Generates a new AI summary draft strictly for the authenticated kiosk patient's encounter.
    """
    session, patient = auth_data
    encounter_id = (session.data or {}).get("encounter_id")

    encounter = None
    if encounter_id:
        try:
            enc_uuid = uuid.UUID(encounter_id)
            encounter = db.query(Encounter).filter(
                Encounter.id == enc_uuid,
                Encounter.patient_id == patient.id
            ).first()
        except ValueError:
            pass

    if not encounter:
        encounter = db.query(Encounter).filter(
            Encounter.patient_id == patient.id,
            Encounter.status.in_(["IN_PROGRESS", "WAITING_FOR_DOCTOR", "COMPLETED"])
        ).order_by(Encounter.start_time.desc()).first()

    if not encounter:
        raise HTTPException(status_code=404, detail="No active encounter found for this session")

    from ai.summarization.aggregator import ClinicalDataAggregator
    from ai.summarization.service import get_summary_provider

    provider = get_summary_provider()
    aggregator = ClinicalDataAggregator(db)
    input_data, source_refs = aggregator.gather_data(str(encounter.id))
    draft = provider.generate(input_data)
    draft.encounter_id = str(encounter.id)
    draft.source_references = source_refs

    existing = db.query(ClinicalSummary).filter(ClinicalSummary.encounter_id == encounter.id).first()
    if existing:
        existing.draft_content = draft.model_dump(mode="json")
        db.commit()
        summary_id = existing.id
    else:
        new_summary = ClinicalSummary(
            encounter_id=encounter.id,
            draft_content=draft.model_dump(mode="json"),
            model_info={"provider": draft.provider, "version": draft.version}
        )
        db.add(new_summary)
        db.commit()
        db.refresh(new_summary)
        summary_id = new_summary.id

    return {"status": "success", "summary_id": str(summary_id), "encounter_id": str(encounter.id)}
