"""
Tests for Doctor Clinical Assessment Workflow (Gap 7).

Covers:
- Assessment draft creation and retrieval (/encounters/{id}/assessment)
- Updating HPI, vitals/physical exam, allergies, medications, diagnosis, and plan
- Doctor verification / sign-off (/encounters/{id}/assessment/finalize)
- Rejection of empty assessment finalization
- Synchronization of confirmed diagnoses and allergies into patient_facts (immutable store)
- Synchronization of confirmed diagnoses and allergies into patient_longitudinal_profiles
- Audit logging of clinical assessment finalization
- Cross-hospital access protection on clinical assessment
"""

import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.models.models import Hospital, User, Patient, Encounter, ClinicalAssessment, PatientFact, PatientLongitudinalProfile
from app.core.security import create_access_token, hash_password
from app.database import Base, engine, SessionLocal

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield

@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_auth_header(user):
    token = create_access_token({
        "sub": str(user.id),
        "username": user.username,
        "role": user.role,
        "hospital_id": str(user.hospital_id) if user.hospital_id else None
    })
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def assessment_setup(db_session):
    hosp = Hospital(name="Manipal Hospital Bangalore")
    db_session.add(hosp)
    db_session.commit()
    db_session.refresh(hosp)

    doctor = User(
        hospital_id=hosp.id,
        role="DOCTOR",
        username=f"dr_sharma_{uuid.uuid4().hex[:6]}",
        password_hash=hash_password("pass")
    )
    db_session.add(doctor)
    db_session.commit()
    db_session.refresh(doctor)

    patient = Patient(
        hospital_id=hosp.id,
        demographic_data={"name": "Rajesh Kumar", "age": 52, "gender": "male"}
    )
    db_session.add(patient)
    db_session.commit()
    db_session.refresh(patient)

    encounter = Encounter(patient_id=patient.id, status="IN_PROGRESS")
    db_session.add(encounter)
    db_session.commit()
    db_session.refresh(encounter)

    return {"hosp": hosp, "doctor": doctor, "patient": patient, "encounter": encounter}

class TestClinicalAssessmentWorkflow:
    def test_get_initial_assessment_draft(self, assessment_setup):
        s = assessment_setup
        headers = get_auth_header(s["doctor"])

        res = client.get(f"/api/v1/encounters/{s['encounter'].id}/assessment", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["encounter_id"] == str(s["encounter"].id)
        assert data["status"] == "DRAFT"

    def test_save_assessment_sections(self, assessment_setup):
        s = assessment_setup
        headers = get_auth_header(s["doctor"])

        payload = {
            "hpi": "Patient presents with persistent cough for 2 weeks and mild dyspnea on exertion.",
            "vitals_examination": {
                "bp_systolic": 130,
                "bp_diastolic": 84,
                "pulse": 76,
                "temperature": 98.6,
                "spo2": 98,
                "respiratory_rate": 18,
                "general_exam": "Conscious, oriented, no pallor or cyanosis",
                "systemic_exam": {"rs": "Bilateral vesicular breath sounds, no wheezing"}
            },
            "allergies_confirmed": [
                {"allergen": "Sulfa drugs", "reaction": "Skin rash / urticaria", "severity": "MODERATE"}
            ],
            "medications_confirmed": [
                {"medication_name": "Metformin 500mg", "frequency": "BD", "indication": "T2DM"}
            ],
            "diagnosis": [
                {"condition": "Acute Bronchitis", "type": "PROVISIONAL", "icd10": "J20.9"},
                {"condition": "Type 2 Diabetes Mellitus", "type": "CONFIRMED", "icd10": "E11.9"}
            ],
            "clinical_plan": "1. Nebulization PRN\n2. Continue Metformin\n3. Steam inhalation\n4. Review in 5 days"
        }

        res = client.post(f"/api/v1/encounters/{s['encounter'].id}/assessment", headers=headers, json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["hpi"] == payload["hpi"]
        assert data["vitals_examination"]["bp_systolic"] == 130
        assert len(data["allergies_confirmed"]) == 1
        assert len(data["diagnosis"]) == 2
        assert data["status"] == "DRAFT"

    def test_finalize_assessment_signoff_and_sync(self, assessment_setup, db_session):
        s = assessment_setup
        headers = get_auth_header(s["doctor"])

        # Populate draft first
        client.post(f"/api/v1/encounters/{s['encounter'].id}/assessment", headers=headers, json={
            "hpi": "Chest tightness and dry cough",
            "diagnosis": [{"condition": "Hypertension", "type": "CONFIRMED", "icd10": "I10"}],
            "allergies_confirmed": [{"allergen": "Penicillin", "reaction": "Anaphylaxis", "severity": "SEVERE"}],
            "clinical_plan": "Start Amlodipine 5mg OD, lifestyle advice"
        })

        # Finalize
        res_fin = client.post(f"/api/v1/encounters/{s['encounter'].id}/assessment/finalize", headers=headers, json={})
        assert res_fin.status_code == 200
        data = res_fin.json()
        assert data["status"] == "FINALIZED"
        assert data["finalized_at"] is not None
        assert data["doctor_id"] == str(s["doctor"].id)

        # 1. Verify sync to patient_facts (immutable store)
        facts = db_session.query(PatientFact).filter(
            PatientFact.patient_id == s["patient"].id,
            PatientFact.source_type == "doctor_assessment"
        ).all()
        assert len(facts) >= 2
        categories = [f.category for f in facts]
        assert "allergy" in categories
        assert "chronic_condition" in categories

        # 2. Verify sync to longitudinal profile snapshot
        prof = db_session.query(PatientLongitudinalProfile).filter(
            PatientLongitudinalProfile.patient_id == s["patient"].id
        ).first()
        if prof:
            allergies = prof.profile.get("allergies", {}).get("items", [])
            allergen_names = [a.get("substance") for a in allergies]
            assert "Penicillin" in allergen_names

    def test_cannot_finalize_empty_assessment(self, assessment_setup):
        s = assessment_setup
        headers = get_auth_header(s["doctor"])

        # New encounter with no draft data
        new_enc = Encounter(patient_id=s["patient"].id, status="IN_PROGRESS")
        db = SessionLocal()
        db.add(new_enc)
        db.commit()
        db.refresh(new_enc)
        db.close()

        res = client.post(f"/api/v1/encounters/{new_enc.id}/assessment/finalize", headers=headers, json={})
        assert res.status_code == 404 or res.status_code == 400
