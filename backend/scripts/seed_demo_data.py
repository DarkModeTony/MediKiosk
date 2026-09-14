import os
import sys
import uuid
from datetime import datetime

# Load env before importing app
env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
if os.path.exists(env_file):
    with open(env_file, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                key, value = line.split("=", 1)
                os.environ[key] = value

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database import SessionLocal
from app.models.models import (
    Patient, Encounter, ClinicalHistory, Symptom, RedFlag,
    Document, DocumentOCR, DocumentEntity, Medication, ClinicalSummary, KioskSession
)

# Deterministic valid UUIDs mapped to canonical demo identities
PAT_RAJ = uuid.UUID("11111111-1111-1111-1111-111111111111")
ENC_RAJ = uuid.UUID("22222222-2222-2222-2222-222222222222")
DOC_RAJ = uuid.UUID("33333333-3333-3333-3333-333333333333")
SUM_RAJ = uuid.UUID("44444444-4444-4444-4444-444444444444")
SES_RAJ = "mock-session-raj-123" # Stored as string in KioskSession.session_token

def seed():
    db = SessionLocal()
    print("Starting database seed...")
    
    try:
        # 1. Patient
        patient = db.query(Patient).filter(Patient.id == PAT_RAJ).first()
        if not patient:
            patient = Patient(
                id=PAT_RAJ,
                demographic_data={"name": "Raj Kumar", "age": 68, "gender": "Male"}
            )
            db.add(patient)
            
        # 2. Session
        session = db.query(KioskSession).filter(KioskSession.session_token == SES_RAJ).first()
        if not session:
            session = KioskSession(
                session_token=SES_RAJ,
                data={"patient_id": str(PAT_RAJ), "language": "hi"}
            )
            db.add(session)

        # 3. Encounter
        encounter = db.query(Encounter).filter(Encounter.id == ENC_RAJ).first()
        if not encounter:
            encounter = Encounter(
                id=ENC_RAJ,
                patient_id=PAT_RAJ,
                status="WAITING"
            )
            db.add(encounter)

        # 4. Clinical History
        history = db.query(ClinicalHistory).filter(ClinicalHistory.encounter_id == ENC_RAJ).first()
        if not history:
            history = ClinicalHistory(
                encounter_id=ENC_RAJ,
                history_data={
                    "facts": {
                        "CHIEF_COMPLAINT": {"field": "CHIEF_COMPLAINT", "value": "Chest pain", "state": "COLLECTED"},
                        "ONSET": {"field": "ONSET", "value": "Today morning", "state": "COLLECTED"},
                        "PAST_MEDICAL_HISTORY": {"field": "PAST_MEDICAL_HISTORY", "value": "Hypertension", "state": "COLLECTED"}
                    }
                }
            )
            db.add(history)

        # 5. Red Flag
        rf = db.query(RedFlag).filter(RedFlag.encounter_id == ENC_RAJ).first()
        if not rf:
            rf = RedFlag(
                encounter_id=ENC_RAJ,
                rule_name="CHEST_PAIN_SUDDEN_ONSET",
                severity="HIGH",
                status="ACTIVE",
                input_evidence={"CHIEF_COMPLAINT": "Chest pain", "ONSET": "Today morning"}
            )
            db.add(rf)
            
        # 6. Document
        doc = db.query(Document).filter(Document.id == DOC_RAJ).first()
        if not doc:
            doc = Document(
                id=DOC_RAJ,
                encounter_id=ENC_RAJ,
                file_path="mock/path.pdf",
                doc_type="Prescription",
                status="COMPLETED"
            )
            db.add(doc)
            
            # OCR
            ocr = DocumentOCR(
                document_id=DOC_RAJ,
                raw_text="Tab Amlodipine 5mg OD\nHb: 10.2",
                status="COMPLETED"
            )
            db.add(ocr)
            
            # Entities
            ent = DocumentEntity(
                document_id=DOC_RAJ,
                entity_type="MEDICATION",
                value={"name": "Amlodipine", "dose": "5 mg", "frequency": "once daily"},
                confidence=0.98,
                status="AI_EXTRACTED",
                source_text="Tab Amlodipine 5mg OD",
                page_number=1
            )
            db.add(ent)
            
            ent2 = DocumentEntity(
                document_id=DOC_RAJ,
                entity_type="LAB_RESULT",
                value={"test": "Hemoglobin", "value": "10.2"},
                confidence=0.95,
                status="AI_EXTRACTED",
                source_text="Hb: 10.2",
                page_number=1
            )
            db.add(ent2)

        # 7. Summary
        summary = db.query(ClinicalSummary).filter(ClinicalSummary.id == SUM_RAJ).first()
        if not summary:
            summary = ClinicalSummary(
                id=SUM_RAJ,
                encounter_id=ENC_RAJ,
                draft_content={
                    "status": "AI_DRAFT",
                    "structured_sections": [
                        {"title": "CHIEF COMPLAINT", "content": "Chest pain"},
                        {"title": "RED FLAGS", "content": "HIGH: CHEST_PAIN_SUDDEN_ONSET"}
                    ]
                }
            )
            db.add(summary)

        db.commit()
        print("Demo Seed Successful! Real database now has Raj Kumar data.")
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
