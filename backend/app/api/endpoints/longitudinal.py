import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Patient, PatientLongitudinalProfile, PatientFact, User
from app.schemas.longitudinal_profile import LongitudinalProfileSchema
from app.api.deps import get_current_user, verify_patient_access

router = APIRouter()

def _create_default_profile(patient: Patient) -> dict:
    """Generates a default Longitudinal Profile (v1.0) seeded with patient demographics."""
    demo = patient.demographic_data or {}
    default_obj = LongitudinalProfileSchema(
        schema_version="1.0",
        patient={
            "patient_id": str(patient.id),
            "name": demo.get("name"),
            "date_of_birth": demo.get("date_of_birth") or demo.get("dob"),
            "age": demo.get("age"),
            "gender": demo.get("gender"),
            "blood_group": demo.get("blood_group"),
        },
        provenance={
            "last_updated": datetime.utcnow().isoformat() + "Z",
            "last_updated_by": "system_init",
            "profile_version": 1
        }
    )
    return default_obj.model_dump()

@router.get("/{patient_id}/longitudinal-profile", response_model=LongitudinalProfileSchema)
def get_longitudinal_profile(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve the patient's longitudinal profile. Auto-creates baseline if not yet present."""
    patient = verify_patient_access(patient_id, current_user, db)

    record = db.query(PatientLongitudinalProfile).filter(
        PatientLongitudinalProfile.patient_id == patient.id
    ).first()

    if not record:
        initial_data = _create_default_profile(patient)
        record = PatientLongitudinalProfile(
            patient_id=patient.id,
            schema_version="1.0",
            profile=initial_data
        )
        db.add(record)
        db.commit()
        db.refresh(record)

    return record.profile

@router.put("/{patient_id}/longitudinal-profile", response_model=LongitudinalProfileSchema)
def update_longitudinal_profile(
    patient_id: str,
    payload: LongitudinalProfileSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Full update/upsert of the patient's longitudinal profile."""
    patient = verify_patient_access(patient_id, current_user, db)

    profile_dict = payload.model_dump()
    # Ensure patient_id in payload matches URL
    profile_dict.setdefault("patient", {})["patient_id"] = str(patient.id)
    
    # Update provenance
    profile_dict.setdefault("provenance", {})
    profile_dict["provenance"]["last_updated"] = datetime.utcnow().isoformat() + "Z"
    curr_version = profile_dict["provenance"].get("profile_version") or 1
    profile_dict["provenance"]["profile_version"] = curr_version + 1

    record = db.query(PatientLongitudinalProfile).filter(
        PatientLongitudinalProfile.patient_id == patient.id
    ).first()

    if record:
        record.profile = profile_dict
        record.schema_version = payload.schema_version
        record.updated_at = datetime.utcnow()
    else:
        record = PatientLongitudinalProfile(
            patient_id=patient.id,
            schema_version=payload.schema_version,
            profile=profile_dict
        )
        db.add(record)

    db.commit()
    db.refresh(record)
    return record.profile

@router.patch("/{patient_id}/longitudinal-profile", response_model=LongitudinalProfileSchema)
def patch_longitudinal_profile(
    patient_id: str,
    patch_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Partial update of the patient's longitudinal profile."""
    patient = verify_patient_access(patient_id, current_user, db)

    record = db.query(PatientLongitudinalProfile).filter(
        PatientLongitudinalProfile.patient_id == patient.id
    ).first()

    current_data = record.profile if record else _create_default_profile(patient)
    
    # Deep merge top-level keys
    for key, value in patch_data.items():
        if key == "schema_version":
            continue
        if isinstance(value, dict) and isinstance(current_data.get(key), dict):
            current_data[key].update(value)
        elif isinstance(value, list) and isinstance(current_data.get(key), list):
            # For lists, optionally append or replace
            current_data[key] = value
        else:
            current_data[key] = value

    # Validate the merged profile through Pydantic
    validated = LongitudinalProfileSchema(**current_data)
    validated_dict = validated.model_dump()
    validated_dict.setdefault("provenance", {})
    validated_dict["provenance"]["last_updated"] = datetime.utcnow().isoformat() + "Z"
    curr_version = validated_dict["provenance"].get("profile_version") or 1
    validated_dict["provenance"]["profile_version"] = curr_version + 1

    if record:
        record.profile = validated_dict
        record.updated_at = datetime.utcnow()
    else:
        record = PatientLongitudinalProfile(
            patient_id=patient.id,
            schema_version=validated.schema_version,
            profile=validated_dict
        )
        db.add(record)

    db.commit()
    db.refresh(record)
    return record.profile

# --- Fact Level Endpoints (Provenance & Auditing) ---

@router.post("/{patient_id}/facts", status_code=status.HTTP_201_CREATED)
def record_patient_fact(
    patient_id: str,
    fact: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Record an individual fact with provenance into patient_facts."""
    patient = verify_patient_access(patient_id, current_user, db)

    new_fact = PatientFact(
        patient_id=patient.id,
        encounter_id=fact.get("encounter_id"),
        category=fact.get("category"),
        fact_type=fact.get("fact_type"),
        body_site=fact.get("body_site"),
        laterality=fact.get("laterality"),
        value=fact.get("value", {}),
        status=fact.get("status", "active"),
        source_type=fact.get("source_type", "patient_statement"),
        source_id=fact.get("source_id"),
        confidence=fact.get("confidence"),
        verified=fact.get("verified", False)
    )
    db.add(new_fact)
    db.commit()
    db.refresh(new_fact)

    return {
        "fact_id": str(new_fact.id),
        "patient_id": str(new_fact.patient_id),
        "status": new_fact.status,
        "verified": new_fact.verified,
        "created_at": new_fact.created_at
    }

@router.get("/{patient_id}/facts")
def list_patient_facts(
    patient_id: str,
    category: Optional[str] = Query(None),
    verified: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List historical facts recorded for a patient."""
    patient = verify_patient_access(patient_id, current_user, db)

    query = db.query(PatientFact).filter(PatientFact.patient_id == patient.id)
    if category:
        query = query.filter(PatientFact.category == category)
    if verified is not None:
        query = query.filter(PatientFact.verified == verified)

    facts = query.order_by(PatientFact.created_at.desc()).all()
    return [
        {
            "id": str(f.id),
            "category": f.category,
            "fact_type": f.fact_type,
            "body_site": f.body_site,
            "laterality": f.laterality,
            "value": f.value,
            "status": f.status,
            "source_type": f.source_type,
            "confidence": f.confidence,
            "verified": f.verified,
            "created_at": f.created_at
        }
        for f in facts
    ]
