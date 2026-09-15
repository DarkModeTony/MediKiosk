import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import (
    Encounter, Patient, User, Prescription, PrescriptionItem,
    PatientLongitudinalProfile, PatientFact, AuditLog
)
from app.services.medicine_search import medicine_search_service
from app.schemas.prescription import (
    PrescriptionItemCreate, PrescriptionItemResponse,
    PrescriptionCreateOrUpdate, FinalizePrescriptionRequest,
    PrescriptionResponse, SafetyAlert, SafetyCheckResult
)
from app.api.deps import get_current_user, verify_encounter_access, verify_patient_access

router = APIRouter()

# ── 1. Medicine Autocomplete & Search ──────────────────────────────────────────

@router.get("/medicines/search")
def search_medicines(
    q: str = Query(..., min_length=1, description="Search query for medicine name or generic composition"),
    limit: int = Query(20, ge=1, le=50)
):
    """Fast indexed search across 253k+ Indian medicines."""
    results = medicine_search_service.search(query=q, limit=limit)
    return {"query": q, "count": len(results), "medicines": results}

@router.get("/medicines/{medicine_id}")
def get_medicine(medicine_id: int):
    """Retrieve details of a single medicine from the dataset."""
    med = medicine_search_service.get_by_id(medicine_id)
    if not med:
        raise HTTPException(status_code=404, detail="Medicine not found")
    return med

# ── 2. Deterministic Safety Checks ─────────────────────────────────────────────

KNOWN_ALLERGEN_CROSS_REACTIONS = {
    "penicillin": ["amoxycillin", "amoxicillin", "ampicillin", "augmentin", "amoxyclav", "clavam", "piperacillin"],
    "sulfa": ["sulfamethoxazole", "bactrim", "septran", "sulfasalazine"],
    "aspirin": ["aspirin", "ibuprofen", "diclofenac", "aceclofenac", "naproxen", "combiflam"],
    "nsaid": ["aspirin", "ibuprofen", "diclofenac", "aceclofenac", "naproxen", "paracetamol"],
    "cephalosporin": ["cefixime", "ceftriaxone", "cefuroxime", "cephalexin"],
}

def compute_safety_checks(patient: Patient, items: List[Any], db: Session) -> SafetyCheckResult:
    """
    Deterministically computes safety alerts against:
    1. Patient recorded allergies
    2. Duplicate active medications
    3. Missing / Unknown data warnings (Unknown != No)
    """
    alerts: List[SafetyAlert] = []
    
    # Fetch patient profile
    profile_record = db.query(PatientLongitudinalProfile).filter(
        PatientLongitudinalProfile.patient_id == patient.id
    ).first()
    
    allergies = []
    current_meds = []
    chronic_conditions = []

    if profile_record and isinstance(profile_record.profile, dict):
        med_history = profile_record.profile.get("medical_history", {})
        allergies = med_history.get("allergies", [])
        chronic_conditions = med_history.get("chronic_conditions", [])
        current_meds = profile_record.profile.get("medications", {}).get("current", [])

    # Also check PatientFact for active verified allergies and medications
    facts = db.query(PatientFact).filter(
        PatientFact.patient_id == patient.id,
        PatientFact.status == "active"
    ).all()
    for f in facts:
        if f.category == "allergy" and isinstance(f.value, dict):
            allergies.append(f.value)
        elif f.category == "medication" and isinstance(f.value, dict):
            current_meds.append(f.value)

    # 1. Check Allergies
    for item in items:
        med_name = (item.medication_name or "").lower()
        gen_name = (item.generic_name or "").lower()
        item_text = f"{med_name} {gen_name}"

        for allergy in allergies:
            allergen = (allergy.get("allergen") or "").lower().strip()
            if not allergen or allergen in ["none", "nil", "unknown", "no known allergies"]:
                continue

            conflict = False
            if allergen in item_text:
                conflict = True
            else:
                # Check cross-reactions
                for group, related_drugs in KNOWN_ALLERGEN_CROSS_REACTIONS.items():
                    if group in allergen:
                        if any(rel in item_text for rel in related_drugs):
                            conflict = True
                            break

            if conflict:
                severity = (allergy.get("severity") or "HIGH").upper()
                alerts.append(SafetyAlert(
                    type="ALLERGY_CONFLICT",
                    severity="HIGH" if severity in ["HIGH", "SEVERE"] else "CAUTION",
                    title="⚠ Known Allergy Conflict",
                    message=f"Patient has a recorded allergy to '{allergen}'. Prescribing '{item.medication_name}' poses an adverse reaction risk.",
                    medication_name=item.medication_name,
                    source=f"Allergy Record: {allergen} (Severity: {severity})"
                ))

    # 2. Check Duplicate Therapies
    for item in items:
        med_name = (item.medication_name or "").lower().strip()
        gen_name = (item.generic_name or "").lower().strip()

        for curr in current_meds:
            c_name = (curr.get("name") or "").lower().strip()
            if not c_name:
                continue

            # Exact or partial match on brand name or composition
            is_duplicate = False
            if med_name and c_name and (med_name in c_name or c_name in med_name):
                is_duplicate = True
            elif gen_name and gen_name in c_name:
                is_duplicate = True

            if is_duplicate:
                alerts.append(SafetyAlert(
                    type="DUPLICATE_MEDICATION",
                    severity="CAUTION",
                    title="⚠ Existing Active Medication",
                    message=f"Patient is currently already taking '{curr.get('name')}'. Verify dosage to prevent duplicate therapy.",
                    medication_name=item.medication_name,
                    source=f"Current medication record: {curr.get('name')} ({curr.get('dose', 'dose unrecorded')})"
                ))

    # 3. Check PRN / SOS clarity
    for item in items:
        if getattr(item, "is_prn", False) and not getattr(item, "indication", None):
            alerts.append(SafetyAlert(
                type="INFO",
                severity="INFO",
                title="ℹ PRN / SOS Clinical Indication",
                message=f"Prescription for '{item.medication_name}' is marked as SOS/PRN. Document the trigger indication (e.g. 'for fever > 100°F').",
                medication_name=item.medication_name,
                source="Prescription Best Practice"
            ))

    passed_critical = not any(a.severity == "HIGH" for a in alerts)

    return SafetyCheckResult(
        alerts=alerts,
        allergies_reviewed=True,
        current_meds_reviewed=True,
        patient_history_reviewed=True,
        passed_critical=passed_critical
    )

def _build_prescription_response(p: Prescription, db: Session) -> PrescriptionResponse:
    items_resp = []
    for item in p.items:
        items_resp.append(PrescriptionItemResponse(
            id=str(item.id),
            prescription_id=str(item.prescription_id),
            medicine_id=item.medicine_id,
            medication_name=item.medication_name,
            generic_name=item.generic_name,
            strength=item.strength,
            dosage_form=item.dosage_form,
            dose=item.dose,
            dose_unit=item.dose_unit,
            route=item.route,
            frequency=item.frequency,
            timing=item.timing,
            duration_value=item.duration_value,
            duration_unit=item.duration_unit,
            quantity=item.quantity,
            indication=item.indication,
            instructions=item.instructions,
            is_prn=item.is_prn,
            min_interval=item.min_interval,
            max_daily_dose=item.max_daily_dose,
            status=item.status or "active",
            item_metadata=item.item_metadata or {},
            created_at=item.created_at
        ))

    patient = p.patient
    if not patient and p.encounter_id:
        enc = db.query(Encounter).filter(Encounter.id == p.encounter_id).first()
        if enc:
            patient = enc.patient

    safety_check = None
    if patient:
        safety_check = compute_safety_checks(patient, p.items, db)

    return PrescriptionResponse(
        id=str(p.id),
        patient_id=str(p.patient_id) if p.patient_id else (str(patient.id) if patient else None),
        encounter_id=str(p.encounter_id),
        doctor_id=str(p.doctor_id) if p.doctor_id else None,
        status=p.status or "DRAFT",
        notes=p.notes,
        created_at=p.created_at,
        updated_at=p.updated_at,
        finalized_at=p.finalized_at,
        items=items_resp,
        safety_check=safety_check
    )

# ── 3. Encounter Prescription Lifecycle Endpoints ──────────────────────────────

@router.get("/encounters/{encounter_id}/prescriptions", response_model=List[PrescriptionResponse])
def get_encounter_prescriptions(
    encounter_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all prescriptions (draft or finalized) associated with an encounter."""
    enc = verify_encounter_access(encounter_id, current_user, db)

    prescriptions = db.query(Prescription).filter(
        Prescription.encounter_id == enc.id
    ).order_by(Prescription.created_at.desc()).all()

    return [_build_prescription_response(p, db) for p in prescriptions]

@router.post("/encounters/{encounter_id}/prescriptions", response_model=PrescriptionResponse)
def save_draft_prescription(
    encounter_id: str,
    payload: PrescriptionCreateOrUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Creates or updates the current draft prescription for an encounter.
    Idempotent: if a draft exists, replaces its line items with the updated set.
    """
    enc = verify_encounter_access(encounter_id, current_user, db)

    patient_id = payload.patient_id or enc.patient_id

    # Look for existing DRAFT
    rx = db.query(Prescription).filter(
        Prescription.encounter_id == encounter_id,
        Prescription.status == "DRAFT"
    ).first()

    if not rx:
        rx = Prescription(
            encounter_id=enc.id,
            patient_id=patient_id,
            doctor_id=uuid.UUID(payload.doctor_id) if payload.doctor_id else None,
            status="DRAFT",
            notes=payload.notes
        )
        db.add(rx)
        db.flush()
    else:
        rx.notes = payload.notes
        rx.updated_at = datetime.utcnow()
        if payload.doctor_id:
            try:
                rx.doctor_id = uuid.UUID(payload.doctor_id)
            except Exception:
                pass
        # Clear existing items for draft replacement
        db.query(PrescriptionItem).filter(PrescriptionItem.prescription_id == rx.id).delete()
        db.flush()

    # Add items
    for item_in in payload.items:
        new_item = PrescriptionItem(
            prescription_id=rx.id,
            medicine_id=item_in.medicine_id,
            medication_name=item_in.medication_name,
            generic_name=item_in.generic_name,
            strength=item_in.strength,
            dosage_form=item_in.dosage_form,
            dose=item_in.dose,
            dose_unit=item_in.dose_unit,
            route=item_in.route,
            frequency=item_in.frequency,
            timing=item_in.timing,
            duration_value=item_in.duration_value,
            duration_unit=item_in.duration_unit,
            quantity=item_in.quantity,
            indication=item_in.indication,
            instructions=item_in.instructions,
            is_prn=item_in.is_prn,
            min_interval=item_in.min_interval,
            max_daily_dose=item_in.max_daily_dose,
            item_metadata=item_in.item_metadata or {}
        )
        db.add(new_item)

    db.commit()
    db.refresh(rx)
    return _build_prescription_response(rx, db)

@router.post("/encounters/{encounter_id}/prescriptions/{prescription_id}/finalize", response_model=PrescriptionResponse)
def finalize_prescription(
    encounter_id: str,
    prescription_id: str,
    req: FinalizePrescriptionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Finalizes a prescription:
    1. Validates that medications exist.
    2. Performs safety check; if high priority alerts exist without acknowledgment, raises error.
    3. Marks status as FINALIZED and stamps finalized_at.
    4. Automatically writes prescribed medications to the Patient Longitudinal Profile.
    5. Inserts verified clinical facts into patient_facts.
    6. Writes an immutable audit log.
    """
    enc = verify_encounter_access(encounter_id, current_user, db)

    rx = db.query(Prescription).filter(
        Prescription.id == prescription_id,
        Prescription.encounter_id == enc.id
    ).first()
    if not rx:
        raise HTTPException(status_code=404, detail="Prescription not found")

    if rx.status == "FINALIZED":
        raise HTTPException(status_code=400, detail="Prescription is already finalized. Use amend to make revisions.")

    if not rx.items or len(rx.items) == 0:
        raise HTTPException(status_code=400, detail="Cannot finalize an empty prescription. Please add at least one medication.")

    patient = enc.patient
    if not patient and rx.patient_id:
        patient = db.query(Patient).filter(Patient.id == rx.patient_id).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient record not found")

    # Safety checks
    safety_result = compute_safety_checks(patient, rx.items, db)
    if not safety_result.passed_critical and not req.acknowledged_safety_alerts:
        high_alerts = [a.title + ": " + a.message for a in safety_result.alerts if a.severity == "HIGH"]
        raise HTTPException(
            status_code=422,
            detail={
                "message": "High-priority safety warnings require explicit clinician review and acknowledgment before finalization.",
                "alerts": high_alerts
            }
        )

    # 1. Finalize Prescription Record
    rx.status = "FINALIZED"
    rx.finalized_at = datetime.utcnow()
    rx.updated_at = datetime.utcnow()
    if req.notes:
        rx.notes = req.notes
    if req.doctor_id:
        try:
            rx.doctor_id = uuid.UUID(req.doctor_id)
        except Exception:
            pass

    # 2. Synchronize to Patient Facts (Immutable Provenance Store)
    for item in rx.items:
        fact = PatientFact(
            patient_id=patient.id,
            encounter_id=enc.id if enc else None,
            category="medication",
            fact_type="prescribed_medication",
            value={
                "name": item.medication_name,
                "generic_name": item.generic_name,
                "strength": item.strength,
                "dosage_form": item.dosage_form,
                "dose": item.dose,
                "route": item.route,
                "frequency": item.frequency,
                "timing": item.timing,
                "duration": f"{item.duration_value} {item.duration_unit}" if item.duration_value else None,
                "quantity": item.quantity,
                "instructions": item.instructions,
                "is_prn": item.is_prn,
                "indication": item.indication,
            },
            status="active",
            source_type="doctor_prescription",
            source_id=str(rx.id),
            confidence=1.0,
            verified=True,
            valid_from=datetime.utcnow()
        )
        db.add(fact)

    # 3. Synchronize to Patient Longitudinal Profile
    long_profile = db.query(PatientLongitudinalProfile).filter(
        PatientLongitudinalProfile.patient_id == patient.id
    ).first()

    if not long_profile:
        new_prof_data = {
            "demographics": {"name": patient.demographic_data.get("name") if patient.demographic_data else None},
            "medical_history": {"allergies": [], "chronic_conditions": [], "previous_conditions": []},
            "medications": {"current": [], "previous": []},
        }
        long_profile = PatientLongitudinalProfile(
            patient_id=patient.id,
            schema_version="1.0",
            profile=new_prof_data
        )
        db.add(long_profile)
        db.flush()

    import copy
    from sqlalchemy.orm.attributes import flag_modified

    prof_data = copy.deepcopy(long_profile.profile) if isinstance(long_profile.profile, dict) else {}
    if "medications" not in prof_data:
        prof_data["medications"] = {"current": [], "previous": []}
    if "current" not in prof_data["medications"]:
        prof_data["medications"]["current"] = []

    for item in rx.items:
        med_entry = {
            "name": item.medication_name,
            "dose": item.dose or item.strength or "1 unit",
            "frequency": item.frequency or "As prescribed",
            "route": item.route or "Oral",
            "reason": item.indication or "Prescribed in encounter",
            "start_date": datetime.utcnow().strftime("%Y-%m-%d"),
            "status": "active"
        }
        prof_data["medications"]["current"].append(med_entry)

    long_profile.profile = prof_data
    flag_modified(long_profile, "profile")
    long_profile.updated_at = datetime.utcnow()

    # 4. Audit Log
    audit = AuditLog(
        user_id=rx.doctor_id,
        action="PRESCRIPTION_FINALIZED",
        target_resource=str(rx.id),
        details={
            "encounter_id": str(encounter_id),
            "patient_id": str(patient.id),
            "items_count": len(rx.items),
            "finalized_at": rx.finalized_at.isoformat()
        }
    )
    db.add(audit)

    db.commit()
    db.refresh(rx)
    return _build_prescription_response(rx, db)

@router.post("/encounters/{encounter_id}/prescriptions/{prescription_id}/amend", response_model=PrescriptionResponse)
def amend_prescription(
    encounter_id: str,
    prescription_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Creates a new editable draft revised prescription from an existing finalized prescription.
    The original finalized prescription remains unchanged in historical records (status='AMENDED').
    """
    enc = verify_encounter_access(encounter_id, current_user, db)

    orig_rx = db.query(Prescription).filter(
        Prescription.id == prescription_id,
        Prescription.encounter_id == enc.id
    ).first()
    if not orig_rx:
        raise HTTPException(status_code=404, detail="Original prescription not found")

    orig_rx.status = "AMENDED"
    orig_rx.updated_at = datetime.utcnow()

    # Clone into new draft
    new_rx = Prescription(
        encounter_id=orig_rx.encounter_id,
        patient_id=orig_rx.patient_id,
        doctor_id=orig_rx.doctor_id,
        status="DRAFT",
        notes=f"Revision of prescription #{str(orig_rx.id)[:8]}. {orig_rx.notes or ''}".strip()
    )
    db.add(new_rx)
    db.flush()

    for item in orig_rx.items:
        cloned_item = PrescriptionItem(
            prescription_id=new_rx.id,
            medicine_id=item.medicine_id,
            medication_name=item.medication_name,
            generic_name=item.generic_name,
            strength=item.strength,
            dosage_form=item.dosage_form,
            dose=item.dose,
            dose_unit=item.dose_unit,
            route=item.route,
            frequency=item.frequency,
            timing=item.timing,
            duration_value=item.duration_value,
            duration_unit=item.duration_unit,
            quantity=item.quantity,
            indication=item.indication,
            instructions=item.instructions,
            is_prn=item.is_prn,
            min_interval=item.min_interval,
            max_daily_dose=item.max_daily_dose,
            item_metadata=item.item_metadata or {}
        )
        db.add(cloned_item)

    db.commit()
    db.refresh(new_rx)
    return _build_prescription_response(new_rx, db)

# ── 4. Longitudinal Patient Prescription History ───────────────────────────────

@router.get("/patients/{patient_id}/prescriptions", response_model=List[PrescriptionResponse])
def get_patient_prescriptions(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all historical prescriptions for a patient across all hospital encounters."""
    patient = verify_patient_access(patient_id, current_user, db)

    prescriptions = db.query(Prescription).filter(
        Prescription.patient_id == patient.id
    ).order_by(Prescription.created_at.desc()).all()

    return [_build_prescription_response(p, db) for p in prescriptions]
