import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class ConflictDetectionResult(BaseModel):
    has_conflict: bool
    conflict_type: Optional[str] = None # "ALLERGY_CONTRADICTION", "CONDITION_CONTRADICTION", "MEDICATION_CONTRADICTION"
    existing_fact_id: Optional[str] = None
    existing_value: Optional[Dict[str, Any]] = None
    candidate_value: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    severity: str = "HIGH" # HIGH or MEDIUM

class FactReconciliationEngine:
    """
    Deterministic clinical fact reconciliation engine.
    Detects semantic contradictions between newly extracted patient facts
    and existing longitudinal/provenance facts.
    
    CRITICAL RULE:
    Verified historical facts must NEVER be silently overwritten.
    Any contradiction must be explicitly flagged for doctor review.
    """

    def check_conflict(
        self,
        candidate_category: str,
        candidate_fact_type: str,
        candidate_value: Dict[str, Any],
        is_negation: bool,
        existing_facts: List[Dict[str, Any]],
    ) -> ConflictDetectionResult:
        """
        Compares a candidate fact against existing facts for the patient.
        
        SAFETY INVARIANT: Unknown ≠ No.
        If existing records show an 'unknown' status for a category (e.g. allergy_status: unknown),
        a new negation statement (e.g. "no allergies") does NOT silently convert unknown to negative.
        It must be flagged for doctor verification.
        """
        cand_val_str = str(candidate_value).lower()

        # ── Unknown ≠ Negative Guard ──
        # If a candidate claims "no known X" but the existing facts explicitly mark
        # the status as "unknown", flag this as a conflict requiring doctor review.
        if is_negation and candidate_category in ("allergy", "chronic_condition", "medication"):
            for ef in existing_facts:
                if ef.get("category") != candidate_category:
                    continue
                ef_val = ef.get("value") or {}
                ef_status = (ef_val.get("status") or ef.get("status", "")).lower()
                if ef_status == "unknown":
                    return ConflictDetectionResult(
                        has_conflict=True,
                        conflict_type=f"{candidate_category.upper()}_UNKNOWN_TO_NEGATIVE",
                        existing_fact_id=str(ef.get("id")),
                        existing_value=ef_val,
                        candidate_value=candidate_value,
                        message=(
                            f"Patient denies {candidate_category}, but existing records show status as 'unknown'. "
                            f"Unknown ≠ No. Requires doctor verification before status can be changed."
                        ),
                        severity="HIGH",
                    )

        # 1. Allergy Conflicts
        if candidate_category == "allergy":
            cand_allergen = (candidate_value.get("allergen") or candidate_value.get("name") or "").lower()
            for ef in existing_facts:
                if ef.get("category") != "allergy":
                    continue
                
                ef_val = ef.get("value") or {}
                ef_allergen = (ef_val.get("allergen") or ef_val.get("name") or "").lower()
                ef_verified = ef.get("verified", False)
                ef_status = ef.get("status", "active")

                if ef_status != "active":
                    continue

                # Case A: Existing has active allergy, but candidate denies it
                if is_negation and cand_allergen and cand_allergen in ef_allergen:
                    return ConflictDetectionResult(
                        has_conflict=True,
                        conflict_type="ALLERGY_CONTRADICTION",
                        existing_fact_id=str(ef.get("id")),
                        existing_value=ef_val,
                        candidate_value=candidate_value,
                        message=f"Patient denies allergy to '{cand_allergen}', but records show verified active allergy.",
                        severity="HIGH" if ef_verified else "MEDIUM",
                    )

                # Case B: Existing says "no known allergies", but candidate reports a specific allergy
                if not is_negation and "no known" in ef_allergen and cand_allergen:
                    return ConflictDetectionResult(
                        has_conflict=True,
                        conflict_type="ALLERGY_CONTRADICTION",
                        existing_fact_id=str(ef.get("id")),
                        existing_value=ef_val,
                        candidate_value=candidate_value,
                        message=f"Patient reports new allergy '{cand_allergen}', contradicting previous 'No known allergies' entry.",
                        severity="HIGH" if ef_verified else "MEDIUM",
                    )

        # 2. Chronic Condition Conflicts
        if candidate_category == "chronic_condition":
            cand_cond = (candidate_value.get("condition") or candidate_value.get("name") or "").lower()
            for ef in existing_facts:
                if ef.get("category") not in ["chronic_condition", "medical_history"]:
                    continue

                ef_val = ef.get("value") or {}
                ef_cond = (ef_val.get("condition") or ef_val.get("name") or "").lower()
                ef_status = ef.get("status", "active")

                if ef_status == "active" and is_negation and cand_cond and cand_cond in ef_cond:
                    return ConflictDetectionResult(
                        has_conflict=True,
                        conflict_type="CONDITION_CONTRADICTION",
                        existing_fact_id=str(ef.get("id")),
                        existing_value=ef_val,
                        candidate_value=candidate_value,
                        message=f"Patient denies having '{cand_cond}', but active verified condition exists in profile.",
                        severity="HIGH",
                    )

        # 3. Medication Conflicts
        if candidate_category == "medication":
            cand_med = (candidate_value.get("medication_name") or candidate_value.get("name") or "").lower()
            for ef in existing_facts:
                if ef.get("category") != "medication":
                    continue

                ef_val = ef.get("value") or {}
                ef_med = (ef_val.get("medication_name") or ef_val.get("name") or "").lower()
                ef_status = ef.get("status", "active")

                if ef_status == "active" and is_negation and cand_med and cand_med in ef_med:
                    return ConflictDetectionResult(
                        has_conflict=True,
                        conflict_type="MEDICATION_CONTRADICTION",
                        existing_fact_id=str(ef.get("id")),
                        existing_value=ef_val,
                        candidate_value=candidate_value,
                        message=f"Patient denies taking active prescribed medication '{cand_med}'.",
                        severity="MEDIUM",
                    )

        return ConflictDetectionResult(has_conflict=False)
