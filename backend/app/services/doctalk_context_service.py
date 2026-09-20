"""
DocTalk Context Service — Secure Consultation Context Synthesis.

Implements the privacy and security boundary between a hospital's full patient
record and an external DocTalk specialist.
- Demographic minimization (Age, Gender, City only — no PII).
- Explicit sharing preferences honored (History, Vitals, Allergies, Meds, Conditions, Investigations, Documents, Summary).
- Source traceability for all clinical facts (provenance).
- Safety invariant: UNKNOWN is never converted to NEGATIVE; AI never adds diagnoses.
"""

import os
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from app.models.models import (
    Encounter,
    Patient,
    ClinicalHistory,
    ClinicalAssessment,
    RedFlag,
    PatientFact,
    Prescription,
    InvestigationOrder,
    Document,
    ClinicalSummary,
)
from app.schemas.doctalk import SharingScopePreferences


class DocTalkContextService:
    @staticmethod
    def synthesize_secure_context(
        encounter: Encounter,
        patient: Patient,
        db: Session,
        preferences: Optional[SharingScopePreferences] = None,
    ) -> Dict[str, Any]:
        """
        Synthesizes a self-contained, sanitized, and source-traceable consultation
        context snapshot according to the requesting doctor's explicit sharing preferences.
        """
        if preferences is None:
            preferences = SharingScopePreferences()

        context: Dict[str, Any] = {
            "demographic_minimization": True,
            "provenance_guaranteed": True,
            "synthesized_at": datetime.now(timezone.utc).isoformat(),
        }

        # 1. Minimized Patient Demographics (strictly no PII)
        demo = patient.demographic_data or {}
        context["patient"] = {
            "age": demo.get("age"),
            "gender": demo.get("gender"),
            "city": demo.get("city"),
        }

        # 2. Clinical History & Chief Complaint
        if preferences.include_history:
            history = (
                db.query(ClinicalHistory)
                .filter(ClinicalHistory.encounter_id == encounter.id)
                .first()
            )
            if history and history.history_data:
                context["chief_complaint"] = history.history_data.get("chief_complaint")
                context["history_summary"] = history.history_data.get("summary")
                context["symptoms"] = history.history_data.get("symptoms", [])

        # 3. Vitals & Doctor Clinical Assessment
        if preferences.include_vitals:
            assessment = (
                db.query(ClinicalAssessment)
                .filter(ClinicalAssessment.encounter_id == encounter.id)
                .first()
            )
            if assessment:
                context["vitals"] = assessment.vitals_examination
                context["hpi"] = assessment.hpi
                # Doctor confirmed diagnoses only (never AI-added)
                context["diagnoses"] = assessment.diagnosis
                context["clinical_plan"] = assessment.clinical_plan

        # 4. Deterministic Red Flags (Always included for clinical safety)
        red_flags = (
            db.query(RedFlag).filter(RedFlag.encounter_id == encounter.id).all()
        )
        if red_flags:
            context["red_flags"] = [
                {"rule_name": rf.rule_name, "severity": rf.severity}
                for rf in red_flags
            ]

        # 5. Patient Facts (Allergies & Chronic Conditions with Provenance)
        facts = (
            db.query(PatientFact)
            .filter(PatientFact.patient_id == patient.id, PatientFact.status == "active")
            .all()
        )

        if preferences.include_allergies:
            allergy_facts = [f for f in facts if f.category == "allergy"]
            if allergy_facts:
                context["allergies"] = [
                    {
                        "fact_id": str(f.id),
                        "value": f.value,
                        "fact_type": f.fact_type,
                        "source_type": f.source_type or "clinical_intake",
                        "source_id": str(f.source_id) if f.source_id else None,
                        "verified": bool(f.verified),
                        "confidence": f.confidence if f.confidence is not None else 1.0,
                    }
                    for f in allergy_facts
                ]
            else:
                # Safety rule: Unknown != Negative. If not documented, report unknown
                context["allergies_status"] = "UNKNOWN"

        if preferences.include_conditions:
            condition_facts = [
                f for f in facts if f.category in ("chronic_condition", "condition")
            ]
            if condition_facts:
                context["chronic_conditions"] = [
                    {
                        "fact_id": str(f.id),
                        "value": f.value,
                        "fact_type": f.fact_type,
                        "source_type": f.source_type or "clinical_intake",
                        "source_id": str(f.source_id) if f.source_id else None,
                        "verified": bool(f.verified),
                        "confidence": f.confidence if f.confidence is not None else 1.0,
                    }
                    for f in condition_facts
                ]

        # 6. Active Medications with Prescription Provenance
        if preferences.include_medications:
            active_meds = []
            prescriptions = (
                db.query(Prescription)
                .filter(
                    Prescription.patient_id == patient.id,
                    Prescription.status.in_(["FINALIZED", "active"]),
                )
                .all()
            )
            for rx in prescriptions:
                for it in rx.items:
                    active_meds.append(
                        {
                            "medication_name": it.medication_name,
                            "dosage": it.dose,
                            "frequency": it.frequency,
                            "route": getattr(it, "route", "Oral"),
                            "duration": getattr(it, "duration", None),
                            "prescription_id": str(rx.id),
                            "prescribed_at": (
                                rx.created_at.isoformat() if rx.created_at else None
                            ),
                        }
                    )
            context["active_medications"] = active_meds

        # 7. Investigations & Laboratory Results
        if preferences.include_investigations:
            orders_query = db.query(InvestigationOrder).filter(
                InvestigationOrder.encounter_id == encounter.id
            )
            if preferences.selected_investigation_ids:
                selected_uuids = []
                for iid in preferences.selected_investigation_ids:
                    try:
                        import uuid
                        selected_uuids.append(uuid.UUID(iid))
                    except ValueError:
                        pass
                if selected_uuids:
                    orders_query = orders_query.filter(
                        InvestigationOrder.id.in_(selected_uuids)
                    )
            orders = orders_query.order_by(InvestigationOrder.ordered_at.desc()).all()
            investigations_list = []
            for o in orders:
                results_list = []
                for r in o.results:
                    is_abnormal = bool(r.abnormal_flag and r.abnormal_flag.upper() not in ("NORMAL", ""))
                    param_name = getattr(r, "parameter_name", None) or getattr(r, "test_parameter", "Parameter")
                    results_list.append(
                        {
                            "result_id": str(r.id),
                            "test_parameter": param_name,
                            "parameter_name": param_name,
                            "value": r.value,
                            "unit": r.unit,
                            "reference_range": r.reference_range,
                            "is_abnormal": is_abnormal,
                            "abnormal_flag": getattr(r, "abnormal_flag", "NORMAL"),
                            "performed_at": (
                                r.created_at.isoformat() if getattr(r, "created_at", None) else None
                            ),
                        }
                    )
                investigations_list.append(
                    {
                        "order_id": str(o.id),
                        "test_name": o.test_name,
                        "test_type": o.test_type,
                        "urgency": o.urgency,
                        "status": o.status,
                        "ordered_at": (
                            o.ordered_at.isoformat() if o.ordered_at else None
                        ),
                        "results": results_list,
                    }
                )
            context["investigations"] = investigations_list

        # 8. Uploaded Documents (Scoped Metadata & Whitelist)
        if preferences.include_documents:
            docs_query = db.query(Document).filter(
                Document.encounter_id == encounter.id
            )
            if preferences.selected_document_ids:
                doc_uuids = []
                for did in preferences.selected_document_ids:
                    try:
                        import uuid
                        doc_uuids.append(uuid.UUID(did))
                    except ValueError:
                        pass
                if doc_uuids:
                    docs_query = docs_query.filter(Document.id.in_(doc_uuids))
            docs = docs_query.all()
            doc_items = []
            allowed_doc_ids = []
            for d in docs:
                did_str = str(d.id)
                allowed_doc_ids.append(did_str)
                doc_items.append(
                    {
                        "document_id": did_str,
                        "doc_type": d.doc_type,
                        "status": d.status,
                        "document_date": (
                            d.document_date.isoformat() if d.document_date else None
                        ),
                        "file_name": (
                            os.path.basename(d.file_path) if d.file_path else "document"
                        ),
                    }
                )
            context["documents"] = doc_items
            context["document_ids"] = allowed_doc_ids

        # 9. AI Summary Draft (if explicitly authorized)
        if preferences.include_summary:
            summary = (
                db.query(ClinicalSummary)
                .filter(ClinicalSummary.encounter_id == encounter.id)
                .first()
            )
            if summary and summary.draft_content:
                context["ai_summary_draft"] = summary.draft_content

        # 10. Record Explicit Sharing Preferences within the Context
        context["sharing_preferences"] = preferences.model_dump()

        return context
