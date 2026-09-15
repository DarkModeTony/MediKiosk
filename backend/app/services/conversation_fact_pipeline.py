import uuid
import copy
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.models.models import PatientFact, PatientLongitudinalProfile, Encounter
from ai.clinical_nlu.service import get_nlu_provider
from ai.clinical_nlu.models import ExtractedFacts, CandidateFact
from ai.reconciliation.engine import FactReconciliationEngine

reconciliation_engine = FactReconciliationEngine()

def process_intake_conversation_facts(
    db: Session,
    patient_id: uuid.UUID,
    encounter_id: uuid.UUID,
    transcript: str,
    question_id: Optional[str] = "general",
    context: Optional[Dict[str, Any]] = None,
) -> List[PatientFact]:
    """
    Complete Conversation -> NLU -> Validation -> Conflict Detection -> Provenance -> patient_facts pipeline.
    
    CRITICAL INVARIANTS:
    - Never diagnose or prescribe autonomously.
    - Verified historical facts are never silently overwritten.
    - Contradictions are tagged as status='conflicted' for doctor review.
    - Source provenance (transcript snippet, question_id) is always attached.
    """
    if not transcript or not transcript.strip():
        return []

    # 1. NLU Candidate Fact Extraction
    provider = get_nlu_provider()
    extracted: ExtractedFacts = provider.extract_candidate_facts(transcript, question_id, context)

    if not extracted.facts:
        return []

    # 2. Query Existing Patient Facts
    existing_fact_rows = db.query(PatientFact).filter(PatientFact.patient_id == patient_id).all()
    existing_facts_list = [
        {
            "id": str(f.id),
            "category": f.category,
            "fact_type": f.fact_type,
            "value": f.value,
            "status": f.status,
            "verified": f.verified,
        }
        for f in existing_fact_rows
    ]

    created_facts: List[PatientFact] = []

    for cand in extracted.facts:
        # 3. Validation: guardrails
        # Non-empty source text required
        if not cand.source_text or not cand.source_text.strip():
            continue
        # Confidence threshold check
        if cand.confidence_score < 0.5:
            continue
        # Prohibit autonomous diagnosis or prescription assignment
        if cand.category in ["diagnosis", "prescription"]:
            continue

        # 4. Conflict Detection
        conflict = reconciliation_engine.check_conflict(
            candidate_category=cand.category,
            candidate_fact_type=cand.fact_type,
            candidate_value=cand.value,
            is_negation=cand.is_negation,
            existing_facts=existing_facts_list,
        )

        fact_status = "conflicted" if conflict.has_conflict else "active"
        fact_value = copy.deepcopy(cand.value)
        if conflict.has_conflict:
            fact_value["_conflict"] = conflict.model_dump()

        # 5. Persist to patient_facts (Immutable Provenance Store)
        new_fact = PatientFact(
            id=uuid.uuid4(),
            patient_id=patient_id,
            encounter_id=encounter_id,
            category=cand.category,
            fact_type=cand.fact_type,
            value=fact_value,
            status=fact_status,
            source_type="kiosk_conversation",
            source_id=f"question:{question_id or 'general'}",
            confidence=cand.confidence_score,
            verified=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(new_fact)
        created_facts.append(new_fact)

    db.flush()

    # 6. Safe Sync to Longitudinal Profile Snapshot (Non-conflicting facts only)
    if created_facts:
        sync_candidate_facts_to_profile(db, patient_id, created_facts)

    return created_facts

def sync_candidate_facts_to_profile(
    db: Session,
    patient_id: uuid.UUID,
    new_facts: List[PatientFact],
):
    """
    Safely integrates non-conflicting facts into the patient longitudinal profile JSONB snapshot.
    Preserves all verified entries and never overwrites existing verified data.
    """
    profile_record = db.query(PatientLongitudinalProfile).filter(
        PatientLongitudinalProfile.patient_id == patient_id
    ).first()

    if not profile_record:
        return

    profile_data = copy.deepcopy(profile_record.profile or {})

    # Ensure sections exist
    if "medical_history" not in profile_data:
        profile_data["medical_history"] = {"allergies": [], "chronic_conditions": []}
    if "allergies" not in profile_data["medical_history"]:
        profile_data["medical_history"]["allergies"] = []
    if "chronic_conditions" not in profile_data["medical_history"]:
        profile_data["medical_history"]["chronic_conditions"] = []

    for fact in new_facts:
        # NEVER sync conflicted facts directly into active profile sections
        if fact.status == "conflicted":
            if "pending_reconciliation" not in profile_data:
                profile_data["pending_reconciliation"] = []
            profile_data["pending_reconciliation"].append({
                "fact_id": str(fact.id),
                "category": fact.category,
                "value": fact.value,
                "source": fact.source_type,
            })
            continue

        # Sync allergy candidate
        if fact.category == "allergy" and not fact.value.get("is_negation"):
            allergen = fact.value.get("allergen") or fact.value.get("name")
            if allergen:
                existing_allergens = [
                    (a.get("allergen") or "").lower()
                    for a in profile_data["medical_history"]["allergies"]
                ]
                if allergen.lower() not in existing_allergens:
                    profile_data["medical_history"]["allergies"].append({
                        "allergen": allergen,
                        "reaction": fact.value.get("reaction", "unspecified"),
                        "severity": "unknown",
                        "status": "active",
                        "verified": False,
                        "source": "kiosk_conversation",
                    })

        # Sync condition candidate
        if fact.category == "chronic_condition" and not fact.value.get("is_negation"):
            cond = fact.value.get("condition") or fact.value.get("name")
            if cond:
                existing_conds = [
                    (c.get("condition") or "").lower()
                    for c in profile_data["medical_history"]["chronic_conditions"]
                ]
                if cond.lower() not in existing_conds:
                    profile_data["medical_history"]["chronic_conditions"].append({
                        "condition": cond,
                        "status": "active",
                        "verified": False,
                        "source": "kiosk_conversation",
                    })

    profile_record.profile = profile_data
    flag_modified(profile_record, "profile")
    profile_record.updated_at = datetime.utcnow()
    db.flush()
