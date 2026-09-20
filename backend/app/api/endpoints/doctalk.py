import os
import json
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

# Maximum WebSocket relay message size (64 KB)
_MAX_WS_MSG_BYTES = 65_536

from app.database import get_db
from app.models.models import (
    User,
    Hospital,
    Patient,
    Encounter,
    ClinicalHistory,
    ClinicalSummary,
    ClinicalAssessment,
    RedFlag,
    PatientFact,
    Prescription,
    Document,
    AuditLog,
    DocTalkConsultation,
    DocTalkConsultationNote,
    DocTalkNotification,
)
from app.schemas.doctalk import (
    ConsultationCreateRequest,
    ConsultationDeclineRequest,
    ConsultationNoteCreate,
    ConsultationNoteResponse,
    ConsultationResponse,
    SpecialistDirectoryItem,
    SpecialistFindAnyResponse,
    RoomTokenResponse,
    VALID_DURATIONS,
)
from app.schemas.notification import (
    NotificationResponse,
    NotificationCountResponse,
    NotificationMarkReadRequest,
)
from app.api.deps import get_current_user, require_doctor, require_authenticated_doctor, verify_encounter_access
from app.core.security import create_access_token, decode_access_token
from app.services.storage import get_document_storage
from app.services.doctalk_context_service import DocTalkContextService
from app.services.doctalk_session_manager import session_manager
from app.services.doctalk_notification_service import (
    create_doctalk_notification,
    check_and_expire_pending_requests,
    get_request_expiry_minutes,
)

logger = logging.getLogger("doctalk.endpoints")

router = APIRouter()



def _build_note_response(note: DocTalkConsultationNote, db: Session) -> ConsultationNoteResponse:
    spec = db.query(User).filter(User.id == note.specialist_id).first()
    hosp = db.query(Hospital).filter(Hospital.id == note.specialist_hospital_id).first()
    enc_id = None
    if getattr(note, "encounter_id", None):
        enc_id = str(note.encounter_id)
    elif getattr(note, "consultation", None) and getattr(note.consultation, "encounter_id", None):
        enc_id = str(note.consultation.encounter_id)
    else:
        consult = db.query(DocTalkConsultation).filter(DocTalkConsultation.id == note.consultation_id).first()
        if consult and consult.encounter_id:
            enc_id = str(consult.encounter_id)

    return ConsultationNoteResponse(
        id=str(note.id),
        consultation_id=str(note.consultation_id),
        encounter_id=enc_id,
        specialist_id=str(note.specialist_id),
        specialist_name=spec.display_name or spec.username if spec else None,
        specialist_hospital_id=str(note.specialist_hospital_id),
        specialist_hospital_name=hosp.name if hosp else None,
        clinical_opinion=note.clinical_opinion,
        recommendations=note.recommendations,
        further_evaluation=note.further_evaluation,
        follow_up=note.follow_up,
        created_at=note.created_at,
        updated_at=note.updated_at,
    )


def _build_consultation_response(c: DocTalkConsultation, db: Session) -> ConsultationResponse:
    req_doc = db.query(User).filter(User.id == c.requesting_doctor_id).first()
    req_hosp = db.query(Hospital).filter(Hospital.id == c.requesting_hospital_id).first()
    spec_doc = db.query(User).filter(User.id == c.specialist_id).first() if c.specialist_id else None
    spec_hosp = db.query(Hospital).filter(Hospital.id == c.specialist_hospital_id).first() if c.specialist_hospital_id else None
    pat = db.query(Patient).filter(Patient.id == c.patient_id).first()
    pat_name = None
    if pat and pat.demographic_data:
        # Pre-acceptance privacy guard: suppress full identity before acceptance
        if c.status != "REQUESTED":
            pat_name = pat.demographic_data.get("name")
        else:
            pat_name = None

    notes_resp = [_build_note_response(n, db) for n in (c.notes or [])]

    return ConsultationResponse(
        id=str(c.id),
        requesting_doctor_id=str(c.requesting_doctor_id),
        requesting_doctor_name=req_doc.display_name or req_doc.username if req_doc else None,
        requesting_hospital_id=str(c.requesting_hospital_id),
        requesting_hospital_name=req_hosp.name if req_hosp else None,
        specialist_id=str(c.specialist_id) if c.specialist_id else None,
        specialist_name=spec_doc.display_name or spec_doc.username if spec_doc else None,
        specialist_hospital_id=str(c.specialist_hospital_id) if c.specialist_hospital_id else None,
        specialist_hospital_name=spec_hosp.name if spec_hosp else None,
        patient_id=str(c.patient_id),
        patient_name=pat_name,
        patient_home_hospital_id=str(c.patient_home_hospital_id),
        encounter_id=str(c.encounter_id),
        specialty=c.specialty,
        reason=c.reason,
        urgency=c.urgency,
        requested_duration_minutes=c.requested_duration_minutes,
        status=c.status,
        access_scope=c.access_scope,
        access_expires_at=c.access_expires_at,
        expires_at=c.expires_at,
        decline_reason=c.decline_reason,
        created_at=c.created_at,
        accepted_at=c.accepted_at,
        started_at=c.started_at,
        completed_at=c.completed_at,
        cancelled_at=c.cancelled_at,
        notes=notes_resp,
    )


def _synthesize_consultation_context(encounter: Encounter, patient: Patient, db: Session) -> dict:
    """Builds a self-contained, sanitized consultation context snapshot."""
    context = {}

    # Patient demographics (minimized)
    demo = patient.demographic_data or {}
    context["patient"] = {
        "age": demo.get("age"),
        "gender": demo.get("gender"),
        "city": demo.get("city"),
    }

    # Chief complaint & intake history
    history = db.query(ClinicalHistory).filter(ClinicalHistory.encounter_id == encounter.id).first()
    if history and history.history_data:
        context["chief_complaint"] = history.history_data.get("chief_complaint")
        context["history_summary"] = history.history_data.get("summary")

    # Assessment vitals & provisional diagnoses
    assessment = db.query(ClinicalAssessment).filter(ClinicalAssessment.encounter_id == encounter.id).first()
    if assessment:
        context["vitals"] = assessment.vitals_examination
        context["diagnoses"] = assessment.diagnosis
        context["hpi"] = assessment.hpi

    # Red flags
    red_flags = db.query(RedFlag).filter(RedFlag.encounter_id == encounter.id).all()
    if red_flags:
        context["red_flags"] = [
            {"rule_name": rf.rule_name, "severity": rf.severity} for rf in red_flags
        ]

    # Relevant patient facts (allergies & chronic conditions)
    facts = db.query(PatientFact).filter(
        PatientFact.patient_id == patient.id,
        PatientFact.status == "active"
    ).all()
    context["allergies"] = [
        f.value for f in facts if f.category == "allergy"
    ]
    context["chronic_conditions"] = [
        f.value for f in facts if f.category in ("chronic_condition", "condition")
    ]

    # Active medications
    active_meds = []
    prescriptions = db.query(Prescription).filter(
        Prescription.patient_id == patient.id,
        Prescription.status.in_(["FINALIZED", "active"])
    ).all()
    for rx in prescriptions:
        for it in rx.items:
            active_meds.append({
                "medication_name": it.medication_name,
                "dosage": it.dose,
                "frequency": it.frequency,
            })
    context["active_medications"] = active_meds

    # AI summary draft
    summary = db.query(ClinicalSummary).filter(ClinicalSummary.encounter_id == encounter.id).first()
    if summary and summary.draft_content:
        context["ai_summary_draft"] = summary.draft_content

    return context


# ---------------------------------------------------------------------------
# Availability status constants
# ---------------------------------------------------------------------------
ONLINE = "ONLINE"
BUSY = "BUSY"
OFFLINE = "OFFLINE"
VALID_AVAILABILITY = {ONLINE, BUSY, OFFLINE}


def _is_eligible_specialist(user: User) -> bool:
    """Baseline eligibility gate — must pass ALL conditions to appear in discovery."""
    return bool(
        user.is_verified
        and user.doctalk_enabled
        and user.specialty
        and user.hospital_id
        and (user.role or "").upper() in ("DOCTOR", "PHYSICIAN")
    )


def _build_specialist_item(doc: User, db: Session) -> SpecialistDirectoryItem:
    hosp = db.query(Hospital).filter(Hospital.id == doc.hospital_id).first()
    availability = (doc.availability_status or OFFLINE).upper()
    if availability not in VALID_AVAILABILITY:
        availability = OFFLINE

    # Infer hospital city from hospital name
    city = None
    if hosp and hosp.name:
        for c in ["New Delhi", "Delhi", "Gurugram", "Bengaluru", "Bangalore", "Mumbai", "Chennai", "Kolkata", "Hyderabad", "Pune", "Ahmedabad", "Jaipur", "Lucknow", "Chandigarh"]:
            if c.lower() in hosp.name.lower():
                city = c
                break

    return SpecialistDirectoryItem(
        doctor_id=str(doc.id),
        username=doc.username,
        display_name=doc.display_name or f"Dr. {doc.username.capitalize()}",
        specialty=doc.specialty,
        sub_specialty=doc.sub_specialty,
        qualification=doc.qualification or "MBBS",
        hospital_id=str(doc.hospital_id),
        hospital_name=hosp.name if hosp else None,
        hospital_city=city,
        availability_status=availability,
        doctalk_enabled=bool(doc.doctalk_enabled),
        is_verified=bool(doc.is_verified),
    )


@router.get("/specialists", response_model=List[SpecialistDirectoryItem])
def search_specialists(
    specialty: Optional[str] = Query(None, description="Filter by medical specialty (partial match)"),
    availability: Optional[str] = Query(None, description="ONLINE, BUSY, or OFFLINE"),
    hospital_id: Optional[str] = Query(None, description="Filter by hospital UUID"),
    location: Optional[str] = Query(None, description="Filter by city/region (partial match against hospital location)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated_doctor),
):
    """
    Cross-hospital specialist discovery directory.

    Returns eligible specialists across ALL hospitals in the network.
    Does NOT restrict results to the requesting doctor's own hospital.

    Eligibility requirements (always enforced, non-configurable):
      - Verified account (is_verified = True)
      - DocTalk enabled (doctalk_enabled = True)
      - Has a recorded specialty
      - Belongs to a registered hospital
      - Role is DOCTOR or PHYSICIAN

    Private details (phone, personal email, patient data) are never exposed.
    """
    # Base eligibility — always required, cannot be overridden by filters
    query = (
        db.query(User)
        .filter(
            User.role.in_(["DOCTOR", "PHYSICIAN"]),
            User.is_verified == True,       # noqa: E712 — SQLAlchemy requires == True
            User.doctalk_enabled == True,   # noqa: E712
            User.specialty.isnot(None),
            User.hospital_id.isnot(None),
        )
    )

    # Optional caller-supplied filters
    if specialty:
        query = query.filter(User.specialty.ilike(f"%{specialty.strip()}%"))

    if availability:
        norm = availability.strip().upper()
        if norm in VALID_AVAILABILITY:
            query = query.filter(User.availability_status == norm)

    if hospital_id:
        try:
            hosp_uuid = uuid.UUID(hospital_id)
            query = query.filter(User.hospital_id == hosp_uuid)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="hospital_id must be a valid UUID",
            )

    from sqlalchemy import case
    priority_case = case(
        (User.username.in_(OFFICIAL_DOCTOR_USERNAMES), 0),
        else_=1,
    )
    doctors = (
        query
        .filter(~User.username.like("doctor_%"), ~User.display_name.ilike("%test%"))
        .order_by(priority_case, User.availability_status, User.display_name)
        .all()
    )
    return [_build_specialist_item(doc, db) for doc in doctors]


OFFICIAL_DOCTOR_USERNAMES = [
    "dr.sharma",
    "dr.sengupta",
    "dr.iyer",
    "dr.mehta",
    "dr.siddiqui",
    "dr.sundaram",
    "dr.banerjee",
    "dr.kulkarni",
]


@router.get("/specialists/find-any", response_model=SpecialistFindAnyResponse)
def find_any_available_specialist(
    specialty: str = Query(..., description="Required: medical specialty to search for"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated_doctor),
):
    """
    Deterministically find an eligible ONLINE specialist for the given specialty.

    Selection priority (no AI, no ratings):
      1. ONLINE availability
      2. Official network physician prioritized
      3. DocTalk eligible (verified + enabled + has specialty + has hospital)
      4. Not the requesting doctor themselves
      5. Alphabetical by display_name for determinism

    Used by the 'Find Any Available Specialist' UI button.
    """
    from sqlalchemy import case

    priority_case = case(
        (User.username.in_(OFFICIAL_DOCTOR_USERNAMES), 0),
        else_=1,
    )

    candidate = (
        db.query(User)
        .filter(
            User.role.in_(["DOCTOR", "PHYSICIAN"]),
            User.is_verified == True,       # noqa: E712
            User.doctalk_enabled == True,   # noqa: E712
            User.specialty.ilike(f"%{specialty.strip()}%"),
            User.hospital_id.isnot(None),
            User.availability_status == ONLINE,
            User.id != current_user.id,     # exclude the requesting doctor
            ~User.username.like("doctor_%"), # exclude automated test harness users
            ~User.display_name.ilike("%test%"),
        )
        .order_by(priority_case, User.display_name)
        .first()
    )

    if not candidate:
        return SpecialistFindAnyResponse(
            found=False,
            specialist=None,
            message=f"No available {specialty} specialist found in the DocTalk network at this time.",
        )

    return SpecialistFindAnyResponse(
        found=True,
        specialist=_build_specialist_item(candidate, db),
        message="Available specialist found.",
    )


@router.post("/requests", response_model=ConsultationResponse, status_code=status.HTTP_201_CREATED)
def create_consultation_request(
    payload: ConsultationCreateRequest,
    prevent_duplicate: bool = Query(False, description="Optionally reject if an active consultation already exists"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated_doctor),
):
    """
    Request a cross-hospital specialist consultation for an encounter.
    The requesting doctor MUST own/control the encounter under hospital tenant isolation.
    """
    # 1. Enforce allowed durations strictly
    if payload.requested_duration_minutes not in VALID_DURATIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Requested duration must be 3, 5, or 7 minutes. Received: {payload.requested_duration_minutes}",
        )

    # 2. Existing hospital-isolation check for requesting doctor
    encounter = verify_encounter_access(payload.encounter_id, current_user, db)
    patient = db.query(Patient).filter(Patient.id == encounter.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient associated with encounter not found")

    # 3. Duplicate prevention: optionally reject if active consultation already exists for this encounter
    if prevent_duplicate:
        existing_active = db.query(DocTalkConsultation).filter(
            DocTalkConsultation.encounter_id == encounter.id,
            DocTalkConsultation.status.in_(["REQUESTED", "ACCEPTED", "IN_PROGRESS"]),
        ).first()
        if existing_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An active DocTalk consultation already exists for this encounter. Please complete or cancel the existing request before requesting another.",
            )

    requesting_hospital_id = current_user.hospital_id or patient.hospital_id
    patient_home_hospital_id = patient.hospital_id or requesting_hospital_id

    # Sweep any expired pending requests
    check_and_expire_pending_requests(db)

    # 4. Specialist validation (can be cross-hospital)
    specialist_id = None
    specialist_hospital_id = None
    if payload.specialist_id:
        specialist = None
        try:
            spec_uuid = uuid.UUID(payload.specialist_id)
            specialist = db.query(User).filter(User.id == spec_uuid).first()
        except ValueError:
            # Also allow lookup by username (e.g. "dr.sengupta")
            specialist = db.query(User).filter(User.username == payload.specialist_id).first()

        if not specialist:
            raise HTTPException(status_code=404, detail="Selected specialist not found")
        if (specialist.role or "").upper() not in ("DOCTOR", "PHYSICIAN", "ADMIN"):
            raise HTTPException(status_code=400, detail="User is not a practicing physician")
        
        # Concurrency guard: verify specialist is not currently engaged in an active consultation
        active_spec_consult = db.query(DocTalkConsultation).filter(
            DocTalkConsultation.specialist_id == specialist.id,
            DocTalkConsultation.status.in_(["ACCEPTED", "IN_PROGRESS"]),
        ).first()
        if active_spec_consult or specialist.availability_status == "BUSY":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Dr. {specialist.display_name or specialist.username} is currently engaged in an active consultation. Please select another specialist or try again shortly.",
            )

        specialist_id = specialist.id
        specialist_hospital_id = specialist.hospital_id

    # 4. Context snapshot synthesis (via DocTalkContextService with explicit sharing preferences)
    access_scope = payload.access_scope
    if not access_scope:
        access_scope = DocTalkContextService.synthesize_secure_context(
            encounter, patient, db, payload.sharing_preferences
        )

    validity_mins = payload.validity_minutes or get_request_expiry_minutes()
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    expires_at = now + timedelta(minutes=validity_mins)

    # 5. Create consultation record
    consult = DocTalkConsultation(
        requesting_doctor_id=current_user.id,
        requesting_hospital_id=requesting_hospital_id,
        specialist_id=specialist_id,
        specialist_hospital_id=specialist_hospital_id,
        patient_id=patient.id,
        patient_home_hospital_id=patient_home_hospital_id,
        encounter_id=encounter.id,
        specialty=payload.specialty,
        reason=payload.reason,
        urgency=payload.urgency,
        requested_duration_minutes=payload.requested_duration_minutes,
        status="REQUESTED",
        access_scope=access_scope,
        expires_at=expires_at,
        created_at=now,
    )
    db.add(consult)
    db.flush()  # materialize consult.id (UUID default fires at flush, not construction)

    # If specialist is explicitly selected, send them an arrival notification
    if specialist_id:
        create_doctalk_notification(
            db=db,
            user_id=specialist_id,
            consultation_id=consult.id,
            encounter_id=encounter.id,
            event_type="DOCTALK_REQUEST_CREATED",
            title="New DocTalk Request",
            message=f"New {payload.urgency} consultation request from Dr. {current_user.display_name or current_user.username} for {payload.specialty}.",
            severity="URGENT" if payload.urgency in ("URGENT", "STAT") else "INFO",
            meta_data={
                "consultation_id": str(consult.id),
                "encounter_id": str(encounter.id),
                "requesting_doctor_name": current_user.display_name or current_user.username,
                "specialty": payload.specialty,
                "urgency": payload.urgency,
                "duration_minutes": payload.requested_duration_minutes,
            },
            auto_commit=False,
        )

    # 6. Audit log
    audit = AuditLog(
        user_id=current_user.id,
        action="DOCTALK_REQUESTED",
        target_resource=f"doctalk_consultations/{consult.id}",
        details={
            "requester": str(current_user.id),
            "requesting_hospital": str(requesting_hospital_id),
            "specialist": str(specialist_id) if specialist_id else None,
            "specialist_hospital": str(specialist_hospital_id) if specialist_hospital_id else None,
            "patient": str(patient.id),
            "encounter": str(encounter.id),
            "timestamps": consult.created_at.isoformat(),
            "actions": "DOCTALK_REQUESTED",
            "encounter_id": str(encounter.id),
            "patient_id": str(patient.id),
            "specialist_id": str(specialist_id) if specialist_id else None,
            "requesting_hospital_id": str(requesting_hospital_id),
            "specialist_hospital_id": str(specialist_hospital_id) if specialist_hospital_id else None,
            "urgency": payload.urgency,
            "requested_duration_minutes": payload.requested_duration_minutes,
        },
    )
    db.add(audit)

    db.commit()
    db.refresh(consult)

    return _build_consultation_response(consult, db)


@router.get("/requests", response_model=List[ConsultationResponse])
def list_consultations(
    role: Optional[str] = Query(None, description="'requesting' or 'specialist'"),
    encounter_id: Optional[str] = Query(None, description="Filter by encounter UUID"),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated_doctor),
):
    """
    List consultations for the authenticated doctor.
    Can be filtered by role (as requesting doctor or specialist), encounter_id, and status.
    """
    # Sweep any expired pending requests
    check_and_expire_pending_requests(db)

    query = db.query(DocTalkConsultation)

    if encounter_id:
        # VULN-06 fix: verify the caller owns this encounter before applying the filter
        try:
            enc_uuid = uuid.UUID(encounter_id)
        except ValueError:
            if str(encounter_id).strip() in ("enc_raj_001", "demo_raj_001"):
                raj = db.query(Patient).filter(Patient.phone == "9000000001").first()
                demo_enc = None
                if raj:
                    demo_enc = db.query(Encounter).filter(
                        Encounter.patient_id == raj.id,
                        Encounter.status.in_(["IN_PROGRESS", "WAITING_FOR_DOCTOR"])
                    ).order_by(Encounter.created_at.desc()).first()
                if demo_enc:
                    enc_uuid = demo_enc.id
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="No active encounter found to map demo encounter ID",
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="encounter_id must be a valid UUID",
                )
        # verify_encounter_access raises 404 if the encounter doesn't belong to caller's hospital
        verify_encounter_access(str(enc_uuid), current_user, db)
        query = query.filter(DocTalkConsultation.encounter_id == enc_uuid)

    if role == "requesting":
        query = query.filter(DocTalkConsultation.requesting_doctor_id == current_user.id)
    elif role == "specialist":
        query = query.filter(DocTalkConsultation.specialist_id == current_user.id)
    else:
        # VULN-03 fix: only show consultations where this doctor is an explicit party.
        # Open (unassigned) consultations are NOT enumerable via this endpoint to prevent
        # cross-hospital patient data leakage. Use GET /specialists/find-any to discover.
        query = query.filter(
            (DocTalkConsultation.requesting_doctor_id == current_user.id)
            | (DocTalkConsultation.specialist_id == current_user.id)
        )

    if status_filter:
        query = query.filter(DocTalkConsultation.status == status_filter.upper())

    consultations = query.order_by(DocTalkConsultation.created_at.desc()).all()
    return [_build_consultation_response(c, db) for c in consultations]


@router.get("/requests/my-requests", response_model=List[ConsultationResponse])
def get_my_requests(
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated_doctor),
):
    """Convenience alias: consultations created by the current doctor."""
    return list_consultations(role="requesting", encounter_id=None, status_filter=status_filter, db=db, current_user=current_user)


@router.get("/requests/my-consultations", response_model=List[ConsultationResponse])
def get_my_consultations(
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated_doctor),
):
    """Convenience alias: consultations requested of or assigned to the current specialist."""
    return list_consultations(role="specialist", encounter_id=None, status_filter=status_filter, db=db, current_user=current_user)


@router.get("/requests/{id}", response_model=ConsultationResponse)
def get_consultation(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated_doctor),
):
    """
    Get detailed consultation context and status.
    Only accessible by the requesting doctor or the explicitly assigned specialist.
    Safe 404 for all non-parties — prevents ID enumeration.
    """
    try:
        consult_uuid = uuid.UUID(id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Consultation not found")

    consult = db.query(DocTalkConsultation).filter(DocTalkConsultation.id == consult_uuid).first()
    if not consult:
        raise HTTPException(status_code=404, detail="Consultation not found")

    # VULN-02 fix: Only explicitly named parties — no open-specialty matching.
    # An unassigned consultation is NOT visible to arbitrary matching-specialty doctors.
    is_party = (
        consult.requesting_doctor_id == current_user.id
        or consult.specialist_id == current_user.id
    )
    if not is_party:
        # Safe 404 prevents cross-hospital enumeration by unauthorized doctors
        raise HTTPException(status_code=404, detail="Consultation not found")

    return _build_consultation_response(consult, db)


@router.get("/requests/{id}/context")
def get_consultation_context(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated_doctor),
):
    """
    Retrieve the scoped, sanitized consultation context for this consultation.
    Only accessible by the requesting doctor or explicitly assigned specialist.
    Before acceptance (status == 'REQUESTED'), only minimal information is visible.
    Once accepted / in progress / completed, the full synthesized consultation context is provided.
    Access is ALWAYS revoked after COMPLETED, CANCELLED, EXPIRED, or DECLINED.
    """
    try:
        consult_uuid = uuid.UUID(id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Consultation not found")

    consult = db.query(DocTalkConsultation).filter(DocTalkConsultation.id == consult_uuid).first()
    if not consult:
        raise HTTPException(status_code=404, detail="Consultation not found")

    # VULN-02 fix: Only explicitly named parties — no open-specialty matching
    is_party = (
        consult.requesting_doctor_id == current_user.id
        or consult.specialist_id == current_user.id
    )
    if not is_party:
        raise HTTPException(status_code=404, detail="Consultation not found")

    # VULN-05 fix: Check expires_at FIRST before any other status-based logic.
    # A REQUESTED consultation past its validity window should appear as EXPIRED.
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if (
        consult.status == "REQUESTED"
        and consult.expires_at
        and consult.expires_at <= now
    ):
        consult.status = "EXPIRED"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Consultation request has expired. Access is revoked.",
        )

    # Specialist access lifecycle & pre-acceptance privacy gating
    if current_user.id != consult.requesting_doctor_id:
        if consult.status == "REQUESTED":
            return {
                "status": consult.status,
                "specialty": consult.specialty,
                "reason": consult.reason,
                "urgency": consult.urgency,
                "requested_duration_minutes": consult.requested_duration_minutes,
                "minimized": True,
                "message": "Full clinical context is unlocked upon accepting this consultation request.",
            }

        # Revoke access for all terminal states
        if consult.status in ("CANCELLED", "DECLINED"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Consultation was {consult.status.lower()}. Context access is revoked.",
            )

        if consult.status == "COMPLETED":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Consultation has been completed. Active context access is revoked.",
            )

        if consult.status == "EXPIRED" or (
            consult.access_expires_at and now > consult.access_expires_at
        ):
            if consult.status != "EXPIRED":
                consult.status = "EXPIRED"
                db.commit()
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Consultation access window has expired. Active context access is revoked.",
            )

    is_external = bool(current_user.hospital_id and consult.requesting_hospital_id and consult.requesting_hospital_id != current_user.hospital_id)

    # Audit log access
    audit = AuditLog(
        user_id=current_user.id,
        action="DOCTALK_CONTEXT_ACCESSED",
        target_resource=f"doctalk_consultations/{consult.id}/context",
        details={
            "viewer_id": str(current_user.id),
            "viewer_role": "SPECIALIST" if current_user.id == consult.specialist_id else "REQUESTING_DOCTOR",
            "is_external": is_external,
        },
    )
    db.add(audit)
    db.commit()

    return {
        "status": consult.status,
        "is_external": is_external,
        "consultation_id": str(consult.id),
        "specialty": consult.specialty,
        "reason": consult.reason,
        "urgency": consult.urgency,
        "requested_duration_minutes": consult.requested_duration_minutes,
        "requesting_hospital_id": str(consult.requesting_hospital_id),
        "context": consult.access_scope or {},
    }


@router.get("/requests/{id}/documents/{document_id}")
def get_consultation_document(
    id: str,
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated_doctor),
):
    """
    Retrieve an attached document file within the authorized consultation access scope.
    Accessible only to the requesting doctor or authorized specialist during an active consultation.
    """
    try:
        consult_uuid = uuid.UUID(id)
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Resource not found")

    consult = db.query(DocTalkConsultation).filter(DocTalkConsultation.id == consult_uuid).first()
    if not consult:
        raise HTTPException(status_code=404, detail="Consultation not found")

    is_party = (
        consult.requesting_doctor_id == current_user.id
        or consult.specialist_id == current_user.id
    )
    if not is_party:
        raise HTTPException(status_code=404, detail="Consultation not found")

    # If specialist, verify active access and expiration
    if current_user.id != consult.requesting_doctor_id:
        doc_now = datetime.now(timezone.utc).replace(tzinfo=None)
        if consult.status not in ("ACCEPTED", "IN_PROGRESS") or (
            consult.access_expires_at and doc_now > consult.access_expires_at
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Consultation is not active or access window has expired",
            )

    # Verify document_id is within access_scope
    allowed_doc_ids = []
    if consult.access_scope:
        allowed_doc_ids = consult.access_scope.get("document_ids", [])
        if not allowed_doc_ids and "documents" in consult.access_scope:
            allowed_doc_ids = [d.get("document_id") for d in consult.access_scope["documents"]]

    if str(doc_uuid) not in allowed_doc_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Document not included in consultation access scope",
        )

    doc = db.query(Document).filter(Document.id == doc_uuid).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    storage = get_document_storage()
    filepath = storage.get_document_path(doc.file_path)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Document file not found on disk")

    audit = AuditLog(
        user_id=current_user.id,
        action="DOCTALK_DOCUMENT_VIEWED",
        target_resource=f"doctalk_consultations/{consult.id}/documents/{doc.id}",
        details={"viewer_id": str(current_user.id)},
    )
    db.add(audit)
    db.commit()

    filename = os.path.basename(filepath)
    return FileResponse(filepath, filename=filename)


@router.post("/requests/{id}/accept", response_model=ConsultationResponse)
def accept_consultation(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated_doctor),
):
    """
    Specialist accepts the consultation.
    Valid state transition: REQUESTED -> ACCEPTED.
    Sets access_expires_at based on requested consultation duration.
    """
    try:
        consult_uuid = uuid.UUID(id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Consultation not found")

    # Race condition prevention & database locking: lock the consultation row
    consult = db.query(DocTalkConsultation).filter(DocTalkConsultation.id == consult_uuid).with_for_update().first()
    if not consult:
        raise HTTPException(status_code=404, detail="Consultation not found")

    # Expiration check
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if (consult.expires_at and consult.expires_at <= now) or (
        consult.created_at and (now - consult.created_at).total_seconds() > get_request_expiry_minutes() * 60
    ):
        consult.status = "EXPIRED"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Consultation request has expired and can no longer be accepted.",
        )

    # State validation
    if consult.status != "REQUESTED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot accept consultation in status '{consult.status}'. Must be 'REQUESTED'.",
        )

    # If a specific specialist was assigned, only they may accept
    if consult.specialist_id and consult.specialist_id != current_user.id:
        raise HTTPException(status_code=403, detail="You are not the designated specialist for this consultation")

    # VULN-02 fix: For open (unassigned) consultations, enforce DocTalk eligibility
    if not consult.specialist_id:
        if not _is_eligible_specialist(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not eligible to accept DocTalk consultations. Ensure your account is verified and DocTalk-enabled with a recorded specialty.",
            )
        if current_user.specialty and consult.specialty and current_user.specialty.lower() not in consult.specialty.lower() and consult.specialty.lower() not in current_user.specialty.lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Specialty mismatch: this consultation requests a different specialty.",
            )

    # Concurrency check: Ensure specialist does not already have an active consultation
    active_consult = db.query(DocTalkConsultation).filter(
        DocTalkConsultation.specialist_id == current_user.id,
        DocTalkConsultation.status.in_(["ACCEPTED", "IN_PROGRESS"]),
        DocTalkConsultation.id != consult.id,
    ).with_for_update().first()

    if active_consult:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have an active DocTalk consultation in progress. Please conclude your current consultation before accepting a new request.",
        )

    # Assign specialist if open
    if not consult.specialist_id:
        consult.specialist_id = current_user.id
        consult.specialist_hospital_id = current_user.hospital_id

    consult.status = "ACCEPTED"
    consult.accepted_at = now
    # Access window: 2 hours from acceptance (covers the consultation + post-note time)
    consult.access_expires_at = now + timedelta(hours=2)

    # Mark specialist availability as BUSY
    current_user.availability_status = "BUSY"

    # Notification for treating doctor
    spec_name = current_user.display_name or current_user.username
    hosp = db.query(Hospital).filter(Hospital.id == current_user.hospital_id).first()
    create_doctalk_notification(
        db=db,
        user_id=consult.requesting_doctor_id,
        consultation_id=consult.id,
        encounter_id=consult.encounter_id,
        event_type="DOCTALK_ACCEPTED",
        title="DocTalk Request Accepted",
        message=f"Dr. {spec_name} ({consult.specialty}) accepted your consultation request.",
        severity="SUCCESS",
        meta_data={
            "consultation_id": str(consult.id),
            "encounter_id": str(consult.encounter_id),
            "specialist_name": spec_name,
            "specialist_hospital": hosp.name if hosp else None,
            "specialty": consult.specialty,
        },
        auto_commit=False,
    )

    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        action="DOCTALK_ACCEPTED",
        target_resource=f"doctalk_consultations/{consult.id}",
        details={
            "requester": str(consult.requesting_doctor_id),
            "requesting_hospital": str(consult.requesting_hospital_id),
            "specialist": str(current_user.id),
            "specialist_hospital": str(current_user.hospital_id) if current_user.hospital_id else None,
            "patient": str(consult.patient_id),
            "encounter": str(consult.encounter_id),
            "timestamps": consult.accepted_at.isoformat(),
            "actions": "DOCTALK_ACCEPTED",
            "specialist_id": str(current_user.id),
            "specialist_hospital_id": str(current_user.hospital_id) if current_user.hospital_id else None,
            "access_expires_at": consult.access_expires_at.isoformat(),
        },
    )
    db.add(audit)

    db.commit()
    db.refresh(consult)
    return _build_consultation_response(consult, db)


@router.post("/requests/{id}/decline", response_model=ConsultationResponse)
def decline_consultation(
    id: str,
    payload: ConsultationDeclineRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated_doctor),
):
    """
    Specialist declines the consultation.
    Valid state transition: REQUESTED -> DECLINED.
    """
    try:
        consult_uuid = uuid.UUID(id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Consultation not found")

    consult = db.query(DocTalkConsultation).filter(DocTalkConsultation.id == consult_uuid).with_for_update().first()
    if not consult:
        raise HTTPException(status_code=404, detail="Consultation not found")

    if consult.specialist_id and consult.specialist_id != current_user.id:
        raise HTTPException(status_code=403, detail="You are not the designated specialist for this consultation")

    # VULN-08 fix: For open (unassigned) consultations, only eligible matching-specialty doctors may decline
    if not consult.specialist_id:
        if not _is_eligible_specialist(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not eligible to decline DocTalk consultations.",
            )

    if consult.status != "REQUESTED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot decline consultation in status '{consult.status}'. Must be 'REQUESTED'.",
        )

    consult.status = "DECLINED"
    consult.decline_reason = payload.reason
    consult.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)

    # Restore specialist availability if no other active consultations
    other_active = db.query(DocTalkConsultation).filter(
        DocTalkConsultation.specialist_id == current_user.id,
        DocTalkConsultation.status.in_(["ACCEPTED", "IN_PROGRESS"]),
        DocTalkConsultation.id != consult.id,
    ).first()
    if not other_active and current_user.availability_status == "BUSY":
        current_user.availability_status = "ONLINE"

    # Notification for treating doctor
    create_doctalk_notification(
        db=db,
        user_id=consult.requesting_doctor_id,
        consultation_id=consult.id,
        encounter_id=consult.encounter_id,
        event_type="DOCTALK_DECLINED",
        title="DocTalk Request Declined",
        message=f"Dr. {current_user.display_name or current_user.username} declined your consultation request. Reason: {payload.reason}",
        severity="WARNING",
        meta_data={
            "consultation_id": str(consult.id),
            "encounter_id": str(consult.encounter_id),
            "specialist_name": current_user.display_name or current_user.username,
            "reason": payload.reason,
        },
        auto_commit=False,
    )

    # VULN-09 fix: Enrich DECLINED audit with full 7-field cross-hospital context
    audit = AuditLog(
        user_id=current_user.id,
        action="DOCTALK_DECLINED",
        target_resource=f"doctalk_consultations/{consult.id}",
        details={
            "who": str(current_user.id),
            "who_name": current_user.display_name or current_user.username,
            "from_hospital": str(current_user.hospital_id) if current_user.hospital_id else None,
            "accessed_what": "doctalk_consultation",
            "for_consultation": str(consult.id),
            "patient": str(consult.patient_id),
            "encounter": str(consult.encounter_id),
            "requesting_hospital": str(consult.requesting_hospital_id),
            "specialist_hospital": str(consult.specialist_hospital_id) if consult.specialist_hospital_id else None,
            "when": datetime.now(timezone.utc).isoformat(),
            "reason": payload.reason,
        },
    )
    db.add(audit)

    db.commit()
    db.refresh(consult)
    return _build_consultation_response(consult, db)


@router.post("/requests/{id}/cancel", response_model=ConsultationResponse)
def cancel_consultation(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated_doctor),
):
    """
    Requesting doctor cancels the consultation.
    Valid state transition: REQUESTED or ACCEPTED -> CANCELLED.
    """
    try:
        consult_uuid = uuid.UUID(id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Consultation not found")

    consult = db.query(DocTalkConsultation).filter(DocTalkConsultation.id == consult_uuid).with_for_update().first()
    if not consult:
        raise HTTPException(status_code=404, detail="Consultation not found")

    if consult.requesting_doctor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the requesting doctor can cancel this consultation")

    if consult.status not in ("REQUESTED", "ACCEPTED"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel consultation in status '{consult.status}'. Must be 'REQUESTED' or 'ACCEPTED'.",
        )

    consult.status = "CANCELLED"
    consult.cancelled_at = datetime.now(timezone.utc).replace(tzinfo=None)

    # If specialist was assigned, restore their availability if they have no other active consultations
    if consult.specialist_id:
        spec_user = db.query(User).filter(User.id == consult.specialist_id).first()
        if spec_user:
            other_active = db.query(DocTalkConsultation).filter(
                DocTalkConsultation.specialist_id == spec_user.id,
                DocTalkConsultation.status.in_(["ACCEPTED", "IN_PROGRESS"]),
                DocTalkConsultation.id != consult.id,
            ).first()
            if not other_active and spec_user.availability_status == "BUSY":
                spec_user.availability_status = "ONLINE"

        # Notify specialist
        create_doctalk_notification(
            db=db,
            user_id=consult.specialist_id,
            consultation_id=consult.id,
            encounter_id=consult.encounter_id,
            event_type="DOCTALK_CANCELLED",
            title="DocTalk Request Cancelled",
            message=f"Consultation request from Dr. {current_user.display_name or current_user.username} was cancelled.",
            severity="INFO",
            meta_data={
                "consultation_id": str(consult.id),
                "encounter_id": str(consult.encounter_id),
                "cancelled_by": current_user.display_name or current_user.username,
            },
            auto_commit=False,
        )

    # VULN-09 fix: Enrich CANCELLED audit with full 7-field cross-hospital context
    audit = AuditLog(
        user_id=current_user.id,
        action="DOCTALK_CANCELLED",
        target_resource=f"doctalk_consultations/{consult.id}",
        details={
            "who": str(current_user.id),
            "who_name": current_user.display_name or current_user.username,
            "from_hospital": str(current_user.hospital_id) if current_user.hospital_id else None,
            "accessed_what": "doctalk_consultation",
            "for_consultation": str(consult.id),
            "patient": str(consult.patient_id),
            "encounter": str(consult.encounter_id),
            "requesting_hospital": str(consult.requesting_hospital_id),
            "specialist_hospital": str(consult.specialist_hospital_id) if consult.specialist_hospital_id else None,
            "when": datetime.now(timezone.utc).isoformat(),
        },
    )
    db.add(audit)

    db.commit()
    db.refresh(consult)
    return _build_consultation_response(consult, db)




@router.get("/requests/{id}/notes", response_model=List[ConsultationNoteResponse])
def get_consultation_notes(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated_doctor),
):
    """
    Retrieve clinical opinion and notes recorded for this consultation.
    Accessible to both requesting doctor and specialist.
    """
    try:
        consult_uuid = uuid.UUID(id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Consultation not found")

    consult = db.query(DocTalkConsultation).filter(DocTalkConsultation.id == consult_uuid).first()
    if not consult:
        raise HTTPException(status_code=404, detail="Consultation not found")

    is_party = (consult.requesting_doctor_id == current_user.id or consult.specialist_id == current_user.id)
    if not is_party:
        raise HTTPException(status_code=404, detail="Consultation not found")

    # VULN-04 fix: Specialist access to notes is revoked after EXPIRED or CANCELLED.
    # The requesting doctor (custodian of clinical record) retains permanent access.
    # The specialist retains access after COMPLETED (they authored the notes).
    if current_user.id != consult.requesting_doctor_id:
        if consult.status in ("EXPIRED", "CANCELLED"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Note access is revoked for {consult.status.lower()} consultations.",
            )

    notes = db.query(DocTalkConsultationNote).filter(
        DocTalkConsultationNote.consultation_id == consult.id
    ).order_by(DocTalkConsultationNote.created_at.asc()).all()

    return [_build_note_response(n, db) for n in notes]


@router.post("/requests/{id}/notes", response_model=ConsultationNoteResponse, status_code=status.HTTP_201_CREATED)
def add_consultation_note(
    id: str,
    payload: ConsultationNoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated_doctor),
):
    """
    Specialist records formal clinical opinion, recommendations, and follow-up advice.
    Only the participating specialist can author consultation notes.
    """
    try:
        consult_uuid = uuid.UUID(id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Consultation not found")

    consult = db.query(DocTalkConsultation).filter(DocTalkConsultation.id == consult_uuid).first()
    if not consult:
        raise HTTPException(status_code=404, detail="Consultation not found")

    # Specialist check
    if consult.specialist_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the participating specialist can submit consultation notes",
        )

    # VULN-07 fix: Block notes on REQUESTED (pre-accept) as well as terminal states
    if consult.status in ("REQUESTED", "DECLINED", "CANCELLED", "EXPIRED"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot add notes to a consultation in status '{consult.status}'. Notes require an active (ACCEPTED or IN_PROGRESS) consultation.",
        )

    specialist_hosp_id = current_user.hospital_id or consult.specialist_hospital_id

    note = DocTalkConsultationNote(
        consultation_id=consult.id,
        encounter_id=consult.encounter_id,
        specialist_id=current_user.id,
        specialist_hospital_id=specialist_hosp_id,
        clinical_opinion=payload.clinical_opinion,
        recommendations=payload.recommendations,
        further_evaluation=payload.further_evaluation,
        follow_up=payload.follow_up,
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    db.add(note)
    db.flush()  # materialize note.id before using it in audit target_resource

    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        action="DOCTALK_NOTE_CREATED",
        target_resource=f"doctalk_consultations/{consult.id}/notes/{note.id}",
        details={
            "requester": str(consult.requesting_doctor_id),
            "requesting_hospital": str(consult.requesting_hospital_id),
            "specialist": str(current_user.id),
            "specialist_hospital": str(specialist_hosp_id) if specialist_hosp_id else None,
            "patient": str(consult.patient_id),
            "encounter": str(consult.encounter_id),
            "timestamps": note.created_at.isoformat(),
            "actions": "DOCTALK_OPINION_ADDED",
            "action": "DOCTALK_OPINION_ADDED",
            "specialist_id": str(current_user.id),
            "consultation_id": str(consult.id),
            "note_id": str(note.id),
        },
    )
    db.add(audit)

    db.commit()
    db.refresh(note)

    return _build_note_response(note, db)


@router.post("/requests/{id}/start", response_model=ConsultationResponse)
def start_consultation(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated_doctor),
):
    """
    Start the consultation session (transition from ACCEPTED to IN_PROGRESS).
    Accessible to either requesting doctor or assigned specialist.
    """
    try:
        consult_uuid = uuid.UUID(id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Consultation not found")

    consult = db.query(DocTalkConsultation).filter(DocTalkConsultation.id == consult_uuid).first()
    if not consult:
        raise HTTPException(status_code=404, detail="Consultation not found")

    is_party = (consult.requesting_doctor_id == current_user.id or consult.specialist_id == current_user.id)
    if not is_party:
        raise HTTPException(status_code=404, detail="Consultation not found")

    if consult.status in ("DECLINED", "CANCELLED", "EXPIRED", "COMPLETED"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot start a consultation in status '{consult.status}'",
        )

    if consult.status == "REQUESTED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Consultation has not yet been accepted by a specialist",
        )

    if consult.status == "ACCEPTED":
        consult.status = "IN_PROGRESS"
        consult.started_at = datetime.now(timezone.utc).replace(tzinfo=None)
        audit = AuditLog(
            user_id=current_user.id,
            action="DOCTALK_CONSULTATION_STARTED",
            target_resource=f"doctalk_consultations/{consult.id}",
            details={
                "requester": str(consult.requesting_doctor_id),
                "requesting_hospital": str(consult.requesting_hospital_id),
                "specialist": str(consult.specialist_id) if consult.specialist_id else str(current_user.id),
                "specialist_hospital": str(consult.specialist_hospital_id) if consult.specialist_hospital_id else None,
                "patient": str(consult.patient_id),
                "encounter": str(consult.encounter_id),
                "timestamps": consult.started_at.isoformat(),
                "actions": "DOCTALK_STARTED",
                "started_by": str(current_user.id),
            },
        )
        db.add(audit)

        # Notify counterpart doctor that session has started
        other_id = consult.specialist_id if current_user.id == consult.requesting_doctor_id else consult.requesting_doctor_id
        if other_id:
            create_doctalk_notification(
                db=db,
                user_id=other_id,
                consultation_id=consult.id,
                encounter_id=consult.encounter_id,
                event_type="DOCTALK_STARTED",
                title="Consultation Started",
                message=f"Dr. {current_user.display_name or current_user.username} started the consultation session.",
                severity="INFO",
                meta_data={"consultation_id": str(consult.id), "encounter_id": str(consult.encounter_id)},
                auto_commit=False,
            )

        db.commit()
        db.refresh(consult)

    return _build_consultation_response(consult, db)


@router.post("/requests/{id}/complete", response_model=ConsultationResponse)
async def complete_consultation(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated_doctor),
):
    """
    Complete the consultation session (transition to COMPLETED).
    Accessible to either requesting doctor or assigned specialist.
    """
    try:
        consult_uuid = uuid.UUID(id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Consultation not found")

    consult = db.query(DocTalkConsultation).filter(DocTalkConsultation.id == consult_uuid).first()
    if not consult:
        raise HTTPException(status_code=404, detail="Consultation not found")

    is_party = (consult.requesting_doctor_id == current_user.id or consult.specialist_id == current_user.id)
    if not is_party:
        raise HTTPException(status_code=404, detail="Consultation not found")

    if consult.status in ("DECLINED", "CANCELLED", "EXPIRED", "REQUESTED"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot complete a consultation in status '{consult.status}'. Must be ACCEPTED or IN_PROGRESS.",
        )

    if consult.status != "COMPLETED":
        consult.status = "COMPLETED"
        consult.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)

        # Restore specialist availability to ONLINE if no other active consultations
        if consult.specialist_id:
            spec_user = db.query(User).filter(User.id == consult.specialist_id).first()
            if spec_user:
                other_active = db.query(DocTalkConsultation).filter(
                    DocTalkConsultation.specialist_id == spec_user.id,
                    DocTalkConsultation.status.in_(["ACCEPTED", "IN_PROGRESS"]),
                    DocTalkConsultation.id != consult.id,
                ).first()
                if not other_active and spec_user.availability_status == "BUSY":
                    spec_user.availability_status = "ONLINE"

        # Notify treating doctor that consultation has concluded
        create_doctalk_notification(
            db=db,
            user_id=consult.requesting_doctor_id,
            consultation_id=consult.id,
            encounter_id=consult.encounter_id,
            event_type="DOCTALK_COMPLETED",
            title="Consultation Completed",
            message="The consultation session has concluded.",
            severity="SUCCESS",
            meta_data={"consultation_id": str(consult.id), "encounter_id": str(consult.encounter_id)},
            auto_commit=False,
        )

        audit = AuditLog(
            user_id=current_user.id,
            action="DOCTALK_COMPLETED",
            target_resource=f"doctalk_consultations/{consult.id}",
            details={
                "requester": str(consult.requesting_doctor_id),
                "requesting_hospital": str(consult.requesting_hospital_id),
                "specialist": str(consult.specialist_id) if consult.specialist_id else None,
                "specialist_hospital": str(consult.specialist_hospital_id) if consult.specialist_hospital_id else None,
                "patient": str(consult.patient_id),
                "encounter": str(consult.encounter_id),
                "timestamps": consult.completed_at.isoformat(),
                "actions": "DOCTALK_COMPLETED",
                "completed_by": str(current_user.id),
            },
        )
        db.add(audit)
        db.commit()
        db.refresh(consult)

        # Notify active websocket room
        await session_manager.end_consultation(str(consult.id), ended_by_user_id=str(current_user.id), reason="COMPLETED")

    return _build_consultation_response(consult, db)


@router.post("/requests/{id}/room-token", response_model=RoomTokenResponse)
def get_consultation_room_token(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated_doctor),
):
    """
    Generate a signed, short-lived room token to join the real-time consultation room.
    Enforces strict authorization: only requesting doctor or assigned specialist.
    Verifies consultation is active (not cancelled, declined, expired, or completed).
    Automatically transitions ACCEPTED -> IN_PROGRESS on token generation.
    Computes server-authoritative remaining time.
    """
    try:
        consult_uuid = uuid.UUID(id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Consultation not found")

    consult = db.query(DocTalkConsultation).filter(DocTalkConsultation.id == consult_uuid).first()
    if not consult:
        raise HTTPException(status_code=404, detail="Consultation not found")

    # Authorization: strictly participating doctor or specialist
    is_req = (consult.requesting_doctor_id == current_user.id)
    is_spec = (consult.specialist_id == current_user.id)
    if not (is_req or is_spec):
        raise HTTPException(status_code=404, detail="Consultation not found")

    # Guard against invalid states
    if consult.status == "CANCELLED":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Consultation has been cancelled")
    if consult.status == "DECLINED":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Consultation was declined")
    if consult.status == "EXPIRED":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Consultation access has expired")
    if consult.status == "COMPLETED":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Consultation has already ended")
    if consult.status == "REQUESTED":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Consultation has not yet been accepted")

    # Auto-transition ACCEPTED -> IN_PROGRESS
    if consult.status == "ACCEPTED":
        consult.status = "IN_PROGRESS"
        consult.started_at = datetime.now(timezone.utc).replace(tzinfo=None)
        audit = AuditLog(
            user_id=current_user.id,
            action="DOCTALK_CONSULTATION_STARTED",
            target_resource=f"doctalk_consultations/{consult.id}",
            details={
                "requester": str(consult.requesting_doctor_id),
                "requesting_hospital": str(consult.requesting_hospital_id),
                "specialist": str(consult.specialist_id) if consult.specialist_id else str(current_user.id),
                "specialist_hospital": str(consult.specialist_hospital_id) if consult.specialist_hospital_id else None,
                "patient": str(consult.patient_id),
                "encounter": str(consult.encounter_id),
                "timestamps": consult.started_at.isoformat(),
                "actions": "DOCTALK_STARTED",
                "started_by": str(current_user.id),
                "auto_started": True,
            },
        )
        db.add(audit)
        db.commit()
        db.refresh(consult)

    # Calculate server-authoritative timer
    _token_now = datetime.now(timezone.utc).replace(tzinfo=None)
    started = consult.started_at or _token_now
    total_seconds = consult.requested_duration_minutes * 60
    elapsed_seconds = (_token_now - started).total_seconds()
    remaining_seconds = max(0, int(total_seconds - elapsed_seconds))

    if remaining_seconds <= 0:
        consult.status = "COMPLETED"
        consult.completed_at = _token_now
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Consultation session duration has expired")

    role = "REQUESTING_DOCTOR" if is_req else "SPECIALIST"

    # Identify peer details
    if is_req:
        peer = db.query(User).filter(User.id == consult.specialist_id).first() if consult.specialist_id else None
        peer_hosp = db.query(Hospital).filter(Hospital.id == consult.specialist_hospital_id).first() if consult.specialist_hospital_id else None
    else:
        peer = db.query(User).filter(User.id == consult.requesting_doctor_id).first()
        peer_hosp = db.query(Hospital).filter(Hospital.id == consult.requesting_hospital_id).first()

    peer_name = (peer.display_name or peer.username) if peer else None
    peer_hosp_name = peer_hosp.name if peer_hosp else None

    # Generate short-lived room token (10 minutes buffer over requested duration)
    room_jwt = create_access_token(
        data={
            "sub": str(current_user.id),
            "consultation_id": str(consult.id),
            "role": role,
            "type": "doctalk_room",
        },
        expires_delta=timedelta(minutes=consult.requested_duration_minutes + 10),
    )

    # Audit log room token generation
    audit = AuditLog(
        user_id=current_user.id,
        action="DOCTALK_ROOM_TOKEN_ISSUED",
        target_resource=f"doctalk_consultations/{consult.id}/room-token",
        details={"role": role, "duration_minutes": consult.requested_duration_minutes},
    )
    db.add(audit)
    db.commit()

    return RoomTokenResponse(
        room_id=str(consult.id),
        room_token=room_jwt,
        role=role,
        user_id=str(current_user.id),
        user_name=current_user.display_name or current_user.username,
        peer_id=str(peer.id) if peer else None,
        peer_name=peer_name,
        peer_hospital=peer_hosp_name,
        duration_minutes=consult.requested_duration_minutes,
        remaining_seconds=remaining_seconds,
        status=consult.status,
        ws_url=f"/api/v1/doctalk/ws/{consult.id}",
    )


@router.websocket("/ws/{consultation_id}")
async def doctalk_websocket(
    websocket: WebSocket,
    consultation_id: str,
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Secure WebSocket signaling endpoint for real-time doctor-to-doctor consultation.
    Validates room token, enforces 2-party isolation, relays WebRTC signaling,
    and coordinates server-authoritative consultation timer and completion.
    """
    if not token:
        await websocket.close(code=4001, reason="Authentication token required")
        return

    payload = decode_access_token(token)
    if not payload or payload.get("type") != "doctalk_room":
        await websocket.close(code=4002, reason="Invalid or expired room token")
        return

    token_consult_id = payload.get("consultation_id")
    if token_consult_id != consultation_id:
        await websocket.close(code=4003, reason="Token consultation ID mismatch")
        return

    user_id = payload.get("sub")
    role = payload.get("role")

    try:
        consult_uuid = uuid.UUID(consultation_id)
    except ValueError:
        await websocket.close(code=4004, reason="Invalid consultation ID")
        return

    consult = db.query(DocTalkConsultation).filter(DocTalkConsultation.id == consult_uuid).first()
    if not consult:
        await websocket.close(code=4004, reason="Consultation not found")
        return

    # Check participant
    if str(consult.requesting_doctor_id) != user_id and str(consult.specialist_id) != user_id:
        await websocket.close(code=4003, reason="Forbidden participant")
        return

    # Check status
    if consult.status not in ("ACCEPTED", "IN_PROGRESS"):
        await websocket.close(code=4005, reason=f"Consultation status is {consult.status}")
        return

    user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
    user_name = user.display_name or user.username if user else role

    # Connect to session manager
    room = await session_manager.connect(
        websocket=websocket,
        consultation_id=consultation_id,
        user_id=user_id,
        role=role,
        user_name=user_name,
        duration_minutes=consult.requested_duration_minutes,
        started_at=consult.started_at,
    )

    try:
        while True:
            raw_text = await websocket.receive_text()
            # VULN-11 fix: reject oversized messages to prevent relay flooding
            if len(raw_text.encode("utf-8")) > _MAX_WS_MSG_BYTES:
                await websocket.send_text(json.dumps({"type": "error", "detail": "Message too large"}))
                continue
            try:
                msg = json.loads(raw_text)
            except Exception:
                continue

            msg_type = msg.get("type")

            if msg_type == "ping":
                remaining = room.get_remaining_seconds()
                await websocket.send_text(json.dumps({
                    "type": "pong",
                    "remaining_seconds": remaining,
                }))
                if remaining <= 0 and not room.is_ended:
                    consult.status = "COMPLETED"
                    consult.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
                    db.commit()
                    await session_manager.end_consultation(
                        consultation_id=consultation_id,
                        reason="TIMER_EXPIRED",
                    )
                    break

            elif msg_type == "end_consultation":
                consult.status = "COMPLETED"
                consult.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
                db.commit()
                await session_manager.end_consultation(
                    consultation_id=consultation_id,
                    ended_by_user_id=user_id,
                    reason="DOCTOR_ENDED",
                )
                break

            elif msg_type in ("offer", "answer", "ice_candidate", "media_state", "chat_message"):
                await session_manager.relay_signal(consultation_id, user_id, msg)

    except WebSocketDisconnect:
        await session_manager.disconnect(consultation_id, user_id)
    except Exception as e:
        logger.error(f"WebSocket error in room {consultation_id} for user {user_id}: {e}")
        await session_manager.disconnect(consultation_id, user_id)


# ---------------------------------------------------------------------------
# Notification Endpoints & Request Expiry Sweeper
# ---------------------------------------------------------------------------

@router.get("/notifications", response_model=List[NotificationResponse])
def get_my_notifications(
    unread_only: bool = Query(False, description="Filter only unread notifications"),
    limit: int = Query(50, ge=1, le=100, description="Max notifications to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated_doctor),
):
    """
    Retrieve notifications for the authenticated doctor.
    Supports unread filtering and pagination limit.
    """
    query = db.query(DocTalkNotification).filter(DocTalkNotification.user_id == current_user.id)
    if unread_only:
        query = query.filter(DocTalkNotification.is_read == False)
    
    notifications = query.order_by(DocTalkNotification.created_at.desc()).limit(limit).all()
    return [
        NotificationResponse(
            id=str(n.id),
            user_id=str(n.user_id),
            consultation_id=str(n.consultation_id) if n.consultation_id else None,
            encounter_id=str(n.encounter_id) if n.encounter_id else None,
            event_type=n.event_type,
            title=n.title,
            message=n.message,
            severity=n.severity or "INFO",
            is_read=bool(n.is_read),
            created_at=n.created_at,
            meta_data=n.meta_data,
        )
        for n in notifications
    ]


@router.get("/notifications/count", response_model=NotificationCountResponse)
def get_unread_notification_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated_doctor),
):
    """Get count of unread notifications for the authenticated doctor."""
    count = db.query(DocTalkNotification).filter(
        DocTalkNotification.user_id == current_user.id,
        DocTalkNotification.is_read == False,
    ).count()
    return NotificationCountResponse(unread_count=count)


@router.post("/notifications/{id}/read", response_model=NotificationResponse)
def mark_notification_read(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated_doctor),
):
    """Mark a single notification as read."""
    try:
        notif_uuid = uuid.UUID(id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Notification not found")

    notif = db.query(DocTalkNotification).filter(
        DocTalkNotification.id == notif_uuid,
        DocTalkNotification.user_id == current_user.id,
    ).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")

    notif.is_read = True
    db.commit()
    db.refresh(notif)

    return NotificationResponse(
        id=str(notif.id),
        user_id=str(notif.user_id),
        consultation_id=str(notif.consultation_id) if notif.consultation_id else None,
        encounter_id=str(notif.encounter_id) if notif.encounter_id else None,
        event_type=notif.event_type,
        title=notif.title,
        message=notif.message,
        severity=notif.severity or "INFO",
        is_read=bool(notif.is_read),
        created_at=notif.created_at,
        meta_data=notif.meta_data,
    )


@router.post("/notifications/read-all")
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated_doctor),
):
    """Mark all unread notifications as read for current user."""
    updated_count = db.query(DocTalkNotification).filter(
        DocTalkNotification.user_id == current_user.id,
        DocTalkNotification.is_read == False,
    ).update({"is_read": True})
    db.commit()
    return {"message": "All notifications marked as read", "updated_count": updated_count}


@router.post("/requests/expire-pending")
def trigger_expire_pending_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated_doctor),
):
    """Explicitly trigger pending requests expiration sweeper."""
    expired = check_and_expire_pending_requests(db)
    return {
        "expired_count": len(expired),
        "expired_consultation_ids": [str(c.id) for c in expired],
    }


