"""
seed_demo_data.py — Seeds Raj Kumar demo patient into the MediPlatform database.

Run from backend/ directory:
    python seed_demo_data.py

Creates:
  - Apollo Hospitals (demo hospital)
  - Dr. Priya Sharma (demo doctor, username: dr.sharma / password: demo1234)
  - Raj Kumar (42M, Delhi) — demo patient with full medical history
  - Active encounter: Fever & weakness x3 days, BP 148/92
  - Longitudinal profile: T2DM, Hypertension, Penicillin allergy, medications
  - Patient facts: allergies, conditions, medications (with provenance)
  - Clinical summary (AI draft)
  - MEDIUM red flag: elevated BP in known hypertensive
"""
import sys
import os
import uuid
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal
from app.models.models import (
    Hospital, User, Patient, Encounter, ClinicalHistory,
    Symptom, ClinicalSummary, RedFlag,
    PatientLongitudinalProfile, PatientFact,
)
from app.core.security import hash_password

def utcnow():
    return datetime.now(timezone.utc)

def seed():
    db = SessionLocal()
    try:
        print("=== MediPlatform Demo Seed ===")

        # ─── Hospital ──────────────────────────────────────────────────────────
        hospital = db.query(Hospital).filter(Hospital.name == "Apollo Hospitals Delhi").first()
        if not hospital:
            hospital = Hospital(name="Apollo Hospitals Delhi")
            db.add(hospital)
            db.commit()
            db.refresh(hospital)
            print(f"[+] Hospital created: {hospital.name} ({hospital.id})")
        else:
            print(f"[=] Hospital exists: {hospital.name}")

        # ─── Doctor ───────────────────────────────────────────────────────────
        doctor = db.query(User).filter(User.username == "dr.sharma").first()
        if not doctor:
            doctor = User(
                username="dr.sharma",
                password_hash=hash_password("demo1234"),
                role="DOCTOR",
                hospital_id=hospital.id,
            )
            db.add(doctor)
            db.commit()
            db.refresh(doctor)
            print(f"[+] Doctor created: {doctor.username} / demo1234")
        else:
            print(f"[=] Doctor exists: {doctor.username}")

        # ─── Patient ──────────────────────────────────────────────────────────
        existing_patient = None
        for p in db.query(Patient).filter(Patient.hospital_id == hospital.id).all():
            demo = p.demographic_data or {}
            if demo.get("name") == "Raj Kumar" and demo.get("phone") == "9000000001":
                existing_patient = p
                break

        if existing_patient:
            patient = existing_patient
            print(f"[=] Patient exists: Raj Kumar ({patient.id})")
        else:
            patient = Patient(
                hospital_id=hospital.id,
                demographic_data={
                    "name": "Raj Kumar",
                    "age": 42,
                    "gender": "Male",
                    "phone": "9000000001",
                    "blood_group": "B+",
                    "city": "Delhi",
                    "preferred_language": "Hindi",
                    "communication_mode": "Voice",
                },
            )
            db.add(patient)
            db.commit()
            db.refresh(patient)
            print(f"[+] Patient created: Raj Kumar ({patient.id})")

        # ─── Encounter ────────────────────────────────────────────────────────
        encounter = None
        for e in db.query(Encounter).filter(
            Encounter.patient_id == patient.id,
            Encounter.status == "WAITING_FOR_DOCTOR",
        ).all():
            encounter = e
            break

        if not encounter:
            encounter = Encounter(
                patient_id=patient.id,
                status="WAITING_FOR_DOCTOR",
                start_time=utcnow(),
            )
            db.add(encounter)
            db.commit()
            db.refresh(encounter)
            print(f"[+] Encounter created ({encounter.id})")
        else:
            print(f"[=] Encounter exists ({encounter.id})")

        # Clinical history
        if not db.query(ClinicalHistory).filter(ClinicalHistory.encounter_id == encounter.id).first():
            history = ClinicalHistory(
                encounter_id=encounter.id,
                history_data={
                    "chief_complaint": "Fever and weakness",
                    "duration": "3 days",
                    "symptoms": ["Fever", "General weakness", "Headache", "Reduced appetite"],
                    "severity": "Moderate",
                    "vitals": {
                        "temperature": "101.2 F",
                        "blood_pressure": "148/92 mmHg",
                        "heart_rate": "96 bpm",
                        "spo2": "98%",
                    },
                    "family_history": {"father": "Hypertension", "mother": "Type 2 Diabetes"},
                    "social_history": {
                        "smoking": "Never",
                        "alcohol": "Occasional",
                        "occupation": "Office employee",
                    },
                },
            )
            db.add(history)
            db.commit()
            print(f"[+] History added.")

        # Symptoms
        if db.query(Symptom).filter(Symptom.encounter_id == encounter.id).count() == 0:
            for sym in ["Fever", "General weakness", "Headache", "Reduced appetite"]:
                db.add(Symptom(encounter_id=encounter.id, symptom_name=sym, details={}))
            db.commit()
            print(f"[+] Symptoms added.")

        # Red flag: elevated BP in known hypertensive
        if db.query(RedFlag).filter(RedFlag.encounter_id == encounter.id).count() == 0:
            red_flag = RedFlag(
                encounter_id=encounter.id,
                rule_name="ELEVATED_BP_KNOWN_HYPERTENSIVE",
                severity="MEDIUM",
                input_evidence={
                    "evidence": {
                        "blood_pressure": "148/92 mmHg",
                        "past_history": "Hypertension since 2022",
                        "current_med": "Amlodipine 5 mg OD",
                    },
                    "message": "BP above target in known hypertensive on Amlodipine.",
                },
                status="ACTIVE",
            )
            db.add(red_flag)
            db.commit()
            print(f"[+] Red flag added.")

        # AI Clinical Summary
        if not db.query(ClinicalSummary).filter(ClinicalSummary.encounter_id == encounter.id).first():
            summary = ClinicalSummary(
                encounter_id=encounter.id,
                draft_content={
                    "status": "AI_DRAFT",
                    "structured_sections": [
                        {"title": "CHIEF COMPLAINT",       "section_type": "COMPLAINT",   "content": "Fever (101.2°F) and generalised weakness for 3 days."},
                        {"title": "HISTORY OF PRESENT ILLNESS", "section_type": "HPI",    "content": "Mr Raj Kumar, 42M, office employee, Delhi. 3-day history of low-grade fever (101.2°F), generalised weakness, headache, and reduced appetite. Known T2DM (HbA1c 7.4%, Feb 2026) and Hypertension on Amlodipine — consider secondary infection given poorly controlled diabetes."},
                        {"title": "RELEVANT MEDICAL HISTORY",   "section_type": "HISTORY", "content": "• T2DM — April 2020, active. HbA1c 7.4% (Feb 2026).\n• Hypertension — July 2022, active. BP today 148/92 mmHg.\n• Surgical: Appendectomy (2015, acute appendicitis)."},
                        {"title": "FAMILY HISTORY",        "section_type": "FAMILY",      "content": "Father: Hypertension. Mother: Type 2 Diabetes."},
                        {"title": "SOCIAL HISTORY",        "section_type": "SOCIAL",       "content": "Non-smoker. Occasional alcohol. Office employee. Preferred language: Hindi."},
                        {"title": "ALLERGIES",             "section_type": "ALLERGIES",    "content": "⚠ Penicillin → Skin rash (Moderate severity). Confirmed at kiosk intake."},
                        {"title": "CURRENT MEDICATIONS",   "section_type": "MEDICATIONS",  "content": "1. Metformin 500 mg — Twice daily (active)\n2. Amlodipine 5 mg — Once daily (active)"},
                        {"title": "VITALS",                "section_type": "VITALS",        "content": "Temperature: 101.2°F | BP: 148/92 mmHg | HR: 96 bpm | SpO₂: 98%"},
                        {"title": "ACTIVE RED FLAGS",      "section_type": "ALERTS",        "content": "MEDIUM — ELEVATED_BP_KNOWN_HYPERTENSIVE: BP 148/92 mmHg in known hypertensive on Amlodipine 5 mg OD."},
                        {"title": "SUGGESTED WORKUP",      "section_type": "PLAN",          "content": "• CBC + differential\n• Blood culture (if systemic infection suspected)\n• FBG + HbA1c (glycaemic review)\n• Urine routine & microscopy\n• LFT/RFT baseline (Metformin)"},
                    ],
                },
            )
            db.add(summary)
            db.commit()
            print(f"[+] AI summary added.")

        # ─── Longitudinal Profile ─────────────────────────────────────────────
        profile = db.query(PatientLongitudinalProfile).filter(
            PatientLongitudinalProfile.patient_id == patient.id
        ).first()

        if not profile:
            profile = PatientLongitudinalProfile(
                patient_id=patient.id,
                schema_version="1.0",
                profile={
                    "schema_version": "1.0",
                    "last_updated": utcnow().isoformat(),
                    "medical_history": {
                        "chronic_conditions": [
                            {"condition": "Type 2 Diabetes Mellitus", "icd10": "E11", "since": "2020", "status": "active"},
                            {"condition": "Hypertension", "icd10": "I10", "since": "2022", "status": "active"},
                        ],
                        "surgeries": [
                            {"procedure": "Appendectomy", "year": 2015, "indication": "Acute appendicitis", "status": "completed"},
                        ],
                        "hospitalizations": [
                            {"reason": "Acute appendicitis", "year": 2015},
                        ],
                    },
                    "allergies": {
                        "known": [
                            {"substance": "Penicillin", "reaction": "Skin rash", "severity": "moderate", "confirmed": True},
                        ]
                    },
                    "current_medications": [
                        {"name": "Metformin", "dose": "500 mg", "frequency": "Twice daily", "status": "active"},
                        {"name": "Amlodipine", "dose": "5 mg", "frequency": "Once daily", "status": "active"},
                    ],
                    "family_history": {
                        "father": "Hypertension",
                        "mother": "Type 2 Diabetes Mellitus",
                    },
                    "social_history": {
                        "smoking": "Never",
                        "alcohol": "Occasional",
                        "occupation": "Office employee",
                    },
                    "vitals_last": {
                        "temperature": "101.2 F",
                        "blood_pressure": "148/92 mmHg",
                        "heart_rate": "96 bpm",
                        "spo2": "98%",
                        "recorded_at": utcnow().isoformat(),
                    },
                },
            )
            db.add(profile)
            db.commit()
            print(f"[+] Longitudinal profile created.")
        else:
            print(f"[=] Longitudinal profile exists.")

        # ─── Patient Facts (Provenance Store) ─────────────────────────────────
        existing_facts = db.query(PatientFact).filter(PatientFact.patient_id == patient.id).count()
        if existing_facts == 0:
            facts_to_add = [
                # Allergies
                PatientFact(patient_id=patient.id, category="allergy",    fact_type="drug_allergy",  value={"substance": "Penicillin", "reaction": "Skin rash", "severity": "moderate"},       source_type="KIOSK_INTAKE",  confidence=0.95, verified=False, valid_from=utcnow()),
                # Chronic conditions
                PatientFact(patient_id=patient.id, category="condition",  fact_type="chronic",        value={"condition": "Type 2 Diabetes Mellitus", "icd10": "E11", "since": "2020"},       source_type="KIOSK_INTAKE",  confidence=0.90, verified=False, valid_from=utcnow()),
                PatientFact(patient_id=patient.id, category="condition",  fact_type="chronic",        value={"condition": "Hypertension", "icd10": "I10", "since": "2022"},                    source_type="KIOSK_INTAKE",  confidence=0.90, verified=False, valid_from=utcnow()),
                # Surgical history
                PatientFact(patient_id=patient.id, category="procedure",  fact_type="surgery",        value={"procedure": "Appendectomy", "year": 2015, "indication": "Acute appendicitis"},   source_type="KIOSK_INTAKE",  confidence=0.88, verified=False, valid_from=utcnow()),
                # Medications
                PatientFact(patient_id=patient.id, category="medication", fact_type="current_med",    value={"name": "Metformin", "dose": "500 mg", "frequency": "Twice daily"},               source_type="KIOSK_INTAKE",  confidence=0.92, verified=False, valid_from=utcnow()),
                PatientFact(patient_id=patient.id, category="medication", fact_type="current_med",    value={"name": "Amlodipine", "dose": "5 mg", "frequency": "Once daily"},                 source_type="KIOSK_INTAKE",  confidence=0.92, verified=False, valid_from=utcnow()),
            ]
            for f in facts_to_add:
                db.add(f)
            db.commit()
            print(f"[+] {len(facts_to_add)} patient facts added.")
        else:
            print(f"[=] Patient facts exist ({existing_facts} records).")

        print()
        print("=== Seed Complete ===")
        print(f"  Hospital  : Apollo Hospitals Delhi")
        print(f"  Doctor    : dr.sharma / demo1234")
        print(f"  Patient   : Raj Kumar (42M, Delhi)")
        print(f"  Encounter : WAITING_FOR_DOCTOR — Fever & weakness x3 days")
        print(f"  Red Flag  : MEDIUM — Elevated BP (148/92) in known hypertensive")
        print()
        print("Visit http://localhost:3001/login and click 'Demo Login'")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Seed failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed()
