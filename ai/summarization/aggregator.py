from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.models.models import Encounter, ClinicalHistory, Symptom, RedFlag, Document, DocumentEntity
from .models import ClinicalSummaryInput, SourceReference, SourceType

class ClinicalDataAggregator:
    def __init__(self, db: Session):
        self.db = db

    def gather_data(self, encounter_id: str) -> tuple[ClinicalSummaryInput, List[SourceReference]]:
        encounter = self.db.query(Encounter).filter(Encounter.id == encounter_id).first()
        if not encounter:
            raise ValueError(f"Encounter {encounter_id} not found")

        input_data = ClinicalSummaryInput()
        source_refs = []

        # 1. Encounter / Patient Context
        input_data.patient_context = encounter.patient.demographic_data if encounter.patient else {}
        input_data.encounter_context = {"status": encounter.status, "start_time": encounter.start_time.isoformat() if encounter.start_time else None}

        # 2. Clinical History
        history = self.db.query(ClinicalHistory).filter(ClinicalHistory.encounter_id == encounter_id).first()
        if history and history.history_data:
            hd = history.history_data
            input_data.chief_complaint = hd.get("chief_complaint")
            input_data.history_of_present_illness = hd.get("hpi")
            
            if input_data.chief_complaint:
                source_refs.append(SourceReference(
                    source_type=SourceType.CLINICAL_INTERVIEW,
                    source_id=str(history.id),
                    fact=f"Chief complaint: {input_data.chief_complaint}"
                ))

        # 3. Symptoms
        symptoms = self.db.query(Symptom).filter(Symptom.encounter_id == encounter_id).all()
        for symp in symptoms:
            details = ", ".join([f"{k}: {v}" for k, v in (symp.details or {}).items()])
            fact_text = f"{symp.symptom_name} ({details})" if details else symp.symptom_name
            input_data.symptoms.append(fact_text)
            source_refs.append(SourceReference(
                source_type=SourceType.CLINICAL_INTERVIEW,
                source_id=str(symp.id),
                fact=fact_text
            ))

        # 4. Red Flags
        red_flags = self.db.query(RedFlag).filter(RedFlag.encounter_id == encounter_id).all()
        for rf in red_flags:
            rf_dict = {"rule_name": rf.rule_name, "severity": rf.severity}
            input_data.red_flags.append(rf_dict)
            source_refs.append(SourceReference(
                source_type=SourceType.CLINICAL_INTERVIEW,
                source_id=str(rf.id),
                fact=f"Red Flag: {rf.rule_name} (Severity: {rf.severity})"
            ))

        # 5. Documents & Entities
        documents = self.db.query(Document).filter(Document.encounter_id == encounter_id).all()
        doc_ids = [str(d.id) for d in documents]
        if doc_ids:
            input_data.previous_documents = [d.doc_type for d in documents]
            entities = self.db.query(DocumentEntity).filter(DocumentEntity.document_id.in_(doc_ids)).all()
            
            for ent in entities:
                # Do not treat rejected entities as valid clinical facts
                if ent.status == "REJECTED":
                    continue
                    
                val = ent.value or {}
                fact_str = ""
                
                if ent.entity_type == "MEDICATION":
                    fact_str = f"{val.get('name', 'Unknown Med')} {val.get('strength', '')} {val.get('frequency', '')}".strip()
                    input_data.medications.append(fact_str)
                elif ent.entity_type == "DIAGNOSIS":
                    fact_str = val.get('diagnosis', 'Unknown Diagnosis')
                    input_data.past_medical_history.append(fact_str)
                elif ent.entity_type == "LAB_RESULT":
                    fact_str = f"{val.get('test_name', 'Unknown Lab')}: {val.get('value', '')} {val.get('unit', '')}"
                    if val.get("abnormal_flag"):
                        fact_str += " (ABNORMAL)"
                    input_data.investigations.append(fact_str)
                elif ent.entity_type == "ALLERGY":
                    fact_str = val.get('allergy', 'Unknown')
                    input_data.allergies.append(fact_str)
                elif ent.entity_type == "PROCEDURE":
                    fact_str = val.get('procedure', 'Unknown')
                    input_data.procedures.append(fact_str)
                
                # Setup provenance
                stype = SourceType.PATIENT_CORRECTION if ent.status == "PATIENT_CORRECTED" else SourceType.MEDICAL_DOCUMENT
                if fact_str:
                    source_refs.append(SourceReference(
                        source_type=stype,
                        source_id=str(ent.id),
                        document_id=str(ent.document_id),
                        page_number=ent.page_number,
                        source_text=ent.source_text,
                        fact=fact_str,
                        confidence=ent.confidence
                    ))

        return input_data, source_refs
