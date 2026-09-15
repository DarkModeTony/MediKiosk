import uuid
import copy
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.database import get_db
from app.models.models import (
    Encounter, Patient, User, ClinicalAssessment,
    PatientLongitudinalProfile, PatientFact, AuditLog
)
from app.schemas.assessment import (
    AssessmentSaveRequest, AssessmentFinalizeRequest, AssessmentResponse
)
from app.api.deps import get_current_user, require_doctor, verify_encounter_access

router = APIRouter()

def _build_assessment_response(ass: ClinicalAssessment, patient_id: Optional[str] = None) -> AssessmentResponse:
    return AssessmentResponse(
        id=str(ass.id),
        encounter_id=str(ass.encounter_id),
        patient_id=patient_id,
        doctor_id=str(ass.doctor_id) if ass.doctor_id else None,
        hpi=ass.hpi,
        vitals_examination=ass.vitals_examination or {},
        allergies_confirmed=ass.allergies_confirmed or [],
        medications_confirmed=ass.medications_confirmed or [],
        diagnosis=ass.diagnosis or [],
        clinical_plan=ass.clinical_plan,
        status=ass.status,
        finalized_at=ass.finalized_at,
        created_at=ass.created_at,
        updated_at=ass.updated_at
    )

@router.get("/encounters/{encounter_id}/assessment", response_model=AssessmentResponse)
def get_encounter_assessment(
    encounter_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve the doctor's clinical assessment for an encounter, or create a blank draft."""
    enc = verify_encounter_access(encounter_id, current_user, db)

    ass = db.query(ClinicalAssessment).filter(
        ClinicalAssessment.encounter_id == enc.id
    ).first()

    if not ass:
        # Create an initial draft
        ass = ClinicalAssessment(
            encounter_id=enc.id,
            doctor_id=current_user.id if current_user.role in ("DOCTOR", "PHYSICIAN", "ADMIN") else None,
            status="DRAFT"
        )
        db.add(ass)
        db.commit()
        db.refresh(ass)

    return _build_assessment_response(ass, str(enc.patient_id) if enc.patient_id else None)

@router.post("/encounters/{encounter_id}/assessment", response_model=AssessmentResponse)
def save_assessment_draft(
    encounter_id: str,
    payload: AssessmentSaveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_doctor)
):
    """Save or update clinical assessment draft (HPI, vitals, allergies, meds, diagnosis, plan)."""
    enc = verify_encounter_access(encounter_id, current_user, db)

    ass = db.query(ClinicalAssessment).filter(
        ClinicalAssessment.encounter_id == enc.id
    ).first()

    if not ass:
        ass = ClinicalAssessment(
            encounter_id=enc.id,
            doctor_id=current_user.id,
            status="DRAFT"
        )
        db.add(ass)

    if ass.status == "FINALIZED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assessment is finalized. Use amend to make changes."
        )

    ass.doctor_id = current_user.id
    if payload.hpi is not None:
        ass.hpi = payload.hpi
    if payload.vitals_examination is not None:
        ass.vitals_examination = payload.vitals_examination
    if payload.allergies_confirmed is not None:
        ass.allergies_confirmed = payload.allergies_confirmed
    if payload.medications_confirmed is not None:
        ass.medications_confirmed = payload.medications_confirmed
    if payload.diagnosis is not None:
        ass.diagnosis = payload.diagnosis
    if payload.clinical_plan is not None:
        ass.clinical_plan = payload.clinical_plan

    ass.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(ass)
    return _build_assessment_response(ass, str(enc.patient_id) if enc.patient_id else None)

@router.post("/encounters/{encounter_id}/assessment/finalize", response_model=AssessmentResponse)
def finalize_assessment(
    encounter_id: str,
    payload: AssessmentFinalizeRequest = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_doctor)
):
    """
    Finalize and sign-off clinical assessment by the physician.
    Synchronizes confirmed diagnoses and allergies into patient_facts and longitudinal profile.
    """
    enc = verify_encounter_access(encounter_id, current_user, db)

    ass = db.query(ClinicalAssessment).filter(
        ClinicalAssessment.encounter_id == enc.id
    ).first()

    if not ass:
        raise HTTPException(status_code=404, detail="Clinical assessment draft not found")

    if ass.status == "FINALIZED":
        raise HTTPException(status_code=400, detail="Assessment is already finalized")

    # Validate that at least one clinical section is documented
    if not any([ass.hpi, ass.vitals_examination, ass.diagnosis, ass.clinical_plan]):
        raise HTTPException(
            status_code=400,
            detail="Cannot finalize an empty assessment. Document HPI, examination, diagnosis, or plan."
        )

    ass.status = "FINALIZED"
    ass.doctor_id = current_user.id
    ass.finalized_at = datetime.utcnow()
    ass.updated_at = datetime.utcnow()

    patient = enc.patient
    if patient:
        # 1. Sync confirmed allergies to patient_facts
        for al in (ass.allergies_confirmed or []):
            allergen = al.get("allergen") or al.get("name")
            if allergen:
                fact = PatientFact(
                    patient_id=patient.id,
                    encounter_id=enc.id,
                    category="allergy",
                    fact_type="substance_allergy",
                    value={
                        "substance": allergen,
                        "reaction": al.get("reaction"),
                        "severity": al.get("severity", "MILD")
                    },
                    status="active",
                    source_type="doctor_assessment",
                    source_id=f"assessment:{ass.id}",
                    confidence=1.0,
                    verified=True
                )
                db.add(fact)

        # 2. Sync confirmed diagnoses to patient_facts
        for diag in (ass.diagnosis or []):
            cond = diag.get("condition") or diag.get("name")
            if cond:
                fact = PatientFact(
                    patient_id=patient.id,
                    encounter_id=enc.id,
                    category="chronic_condition",
                    fact_type="diagnosis",
                    value={
                        "condition": cond,
                        "type": diag.get("type", "CONFIRMED"),
                        "icd10": diag.get("icd10")
                    },
                    status="active",
                    source_type="doctor_assessment",
                    source_id=f"assessment:{ass.id}",
                    confidence=1.0,
                    verified=True
                )
                db.add(fact)

        # 3. Update Longitudinal Profile Snapshot
        prof = db.query(PatientLongitudinalProfile).filter(
            PatientLongitudinalProfile.patient_id == patient.id
        ).first()
        if prof and prof.profile:
            updated_p = copy.deepcopy(prof.profile)
            # Update allergies
            if ass.allergies_confirmed:
                updated_p.setdefault("allergies", {})
                updated_p["allergies"]["status"] = "present"
                existing_al = updated_p["allergies"].get("items", [])
                for al in ass.allergies_confirmed:
                    name = al.get("allergen") or al.get("name")
                    if name and not any(e.get("substance") == name for e in existing_al):
                        existing_al.append({
                            "substance": name,
                            "reaction": al.get("reaction"),
                            "severity": al.get("severity", "MILD"),
                            "status": "confirmed"
                        })
                updated_p["allergies"]["items"] = existing_al

            # Update medical history / conditions
            if ass.diagnosis:
                updated_p.setdefault("medical_history", {})
                existing_conds = updated_p["medical_history"].get("conditions", [])
                for d in ass.diagnosis:
                    cond = d.get("condition") or d.get("name")
                    if cond and not any(c.get("name") == cond for c in existing_conds):
                        existing_conds.append({
                            "name": cond,
                            "icd10": d.get("icd10"),
                            "status": "active"
                        })
                updated_p["medical_history"]["conditions"] = existing_conds

            # Provenance
            updated_p.setdefault("provenance", {})
            updated_p["provenance"]["last_updated"] = datetime.utcnow().isoformat() + "Z"
            updated_p["provenance"]["last_updated_by"] = f"doctor:{current_user.id}"
            curr_v = updated_p["provenance"].get("profile_version") or 1
            updated_p["provenance"]["profile_version"] = curr_v + 1

            prof.profile = updated_p
            flag_modified(prof, "profile")

    # 4. Audit Log
    audit = AuditLog(
        user_id=current_user.id,
        action="ASSESSMENT_FINALIZED",
        target_resource=f"assessments/{ass.id}",
        details={
            "encounter_id": str(enc.id),
            "patient_id": str(patient.id) if patient else None,
            "finalized_at": ass.finalized_at.isoformat()
        }
    )
    db.add(audit)

    db.commit()
    db.refresh(ass)
    return _build_assessment_response(ass, str(enc.patient_id) if enc.patient_id else None)
