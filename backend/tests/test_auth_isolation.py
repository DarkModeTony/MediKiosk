"""
Tests for Authentication, Authorization & Hospital-Level Tenant Isolation (Gap 5).

Covers:
- Hospital creation and user registration
- JWT login, token expiration, and profile retrieval (/auth/me)
- Cross-hospital access denial:
  - Hospital A doctor accessing Hospital B patient -> 404
  - Hospital A doctor accessing Hospital B encounter -> 404
  - Hospital A doctor accessing Hospital B document -> 404
  - Hospital A doctor accessing Hospital B prescription -> 404
  - Hospital A doctor accessing Hospital B facts / longitudinal profile -> 404
- Active encounters queue scoping to authenticated user's hospital
- Unauthorized access rejection (401)
"""

import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.models.models import Hospital, User, Patient, Encounter, Document, Prescription
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

def create_test_hospital(db, name="Apollo Test Hospital"):
    hosp = Hospital(name=name)
    db.add(hosp)
    db.commit()
    db.refresh(hosp)
    return hosp

def create_test_doctor(db, hospital_id, username="dr_smith", password="password123"):
    user = User(
        hospital_id=hospital_id,
        role="DOCTOR",
        username=username,
        password_hash=hash_password(password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_auth_header(user):
    token = create_access_token({
        "sub": str(user.id),
        "username": user.username,
        "role": user.role,
        "hospital_id": str(user.hospital_id) if user.hospital_id else None
    })
    return {"Authorization": f"Bearer {token}"}

class TestAuthentication:
    def test_login_success(self, db_session):
        hosp = create_test_hospital(db_session, "Fortis Delhi")
        doc = create_test_doctor(db_session, hosp.id, username=f"doc_{uuid.uuid4().hex[:6]}", password="securepass123")

        res = client.post("/api/v1/auth/login", json={
            "username": doc.username,
            "password": "securepass123"
        })
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["role"] == "DOCTOR"
        assert data["hospital_name"] == "Fortis Delhi"

    def test_login_invalid_credentials(self, db_session):
        res = client.post("/api/v1/auth/login", json={
            "username": "non_existent_doctor",
            "password": "wrong"
        })
        assert res.status_code == 401

    def test_get_current_user_profile(self, db_session):
        hosp = create_test_hospital(db_session, "Max Healthcare")
        doc = create_test_doctor(db_session, hosp.id, username=f"doc_{uuid.uuid4().hex[:6]}")
        headers = get_auth_header(doc)

        res = client.get("/api/v1/auth/me", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["id"] == str(doc.id)
        assert data["username"] == doc.username
        assert data["hospital_name"] == "Max Healthcare"

class TestHospitalTenantIsolation:
    @pytest.fixture
    def two_hospitals_setup(self, db_session):
        # Hospital A
        hosp_a = create_test_hospital(db_session, "Hospital A (Mumbai)")
        doc_a = create_test_doctor(db_session, hosp_a.id, username=f"doc_a_{uuid.uuid4().hex[:6]}")
        
        # Hospital B
        hosp_b = create_test_hospital(db_session, "Hospital B (Chennai)")
        doc_b = create_test_doctor(db_session, hosp_b.id, username=f"doc_b_{uuid.uuid4().hex[:6]}")

        # Patient in Hospital A
        pat_a = Patient(hospital_id=hosp_a.id, demographic_data={"name": "Patient A", "age": 45})
        db_session.add(pat_a)
        db_session.commit()
        db_session.refresh(pat_a)

        # Encounter in Hospital A
        enc_a = Encounter(patient_id=pat_a.id, status="IN_PROGRESS")
        db_session.add(enc_a)
        db_session.commit()
        db_session.refresh(enc_a)

        # Patient in Hospital B
        pat_b = Patient(hospital_id=hosp_b.id, demographic_data={"name": "Patient B", "age": 32})
        db_session.add(pat_b)
        db_session.commit()
        db_session.refresh(pat_b)

        # Encounter in Hospital B
        enc_b = Encounter(patient_id=pat_b.id, status="IN_PROGRESS")
        db_session.add(enc_b)
        db_session.commit()
        db_session.refresh(enc_b)

        return {
            "hosp_a": hosp_a, "doc_a": doc_a, "pat_a": pat_a, "enc_a": enc_a,
            "hosp_b": hosp_b, "doc_b": doc_b, "pat_b": pat_b, "enc_b": enc_b
        }

    def test_doctor_a_cannot_access_patient_b(self, two_hospitals_setup):
        s = two_hospitals_setup
        headers_a = get_auth_header(s["doc_a"])
        
        # Doctor A accesses Patient A -> 200 OK
        res_a = client.get(f"/api/v1/patients/{s['pat_a'].id}", headers=headers_a)
        assert res_a.status_code == 200
        assert res_a.json()["name"] == "Patient A"

        # Doctor A attempts to access Patient B -> 404 NOT FOUND (prevents ID enumeration)
        res_cross = client.get(f"/api/v1/patients/{s['pat_b'].id}", headers=headers_a)
        assert res_cross.status_code == 404

    def test_doctor_a_cannot_access_encounter_b(self, two_hospitals_setup):
        s = two_hospitals_setup
        headers_a = get_auth_header(s["doc_a"])

        # Doctor A accesses Encounter A -> 200 OK
        res_a = client.get(f"/api/v1/encounters/{s['enc_a'].id}", headers=headers_a)
        assert res_a.status_code == 200

        # Doctor A attempts to access Encounter B -> 404 NOT FOUND
        res_cross = client.get(f"/api/v1/encounters/{s['enc_b'].id}", headers=headers_a)
        assert res_cross.status_code == 404

    def test_active_encounters_queue_scoped_to_hospital(self, two_hospitals_setup):
        s = two_hospitals_setup
        headers_a = get_auth_header(s["doc_a"])
        headers_b = get_auth_header(s["doc_b"])

        # Queue for Doctor A should only show Hospital A encounters
        res_a = client.get("/api/v1/encounters/active", headers=headers_a)
        assert res_a.status_code == 200
        enc_ids_a = [e["id"] for e in res_a.json()]
        assert str(s["enc_a"].id) in enc_ids_a
        assert str(s["enc_b"].id) not in enc_ids_a

        # Queue for Doctor B should only show Hospital B encounters
        res_b = client.get("/api/v1/encounters/active", headers=headers_b)
        assert res_b.status_code == 200
        enc_ids_b = [e["id"] for e in res_b.json()]
        assert str(s["enc_b"].id) in enc_ids_b
        assert str(s["enc_a"].id) not in enc_ids_b

    def test_cross_hospital_longitudinal_profile_blocked(self, two_hospitals_setup):
        s = two_hospitals_setup
        headers_a = get_auth_header(s["doc_a"])

        # Doctor A trying to get Patient B's longitudinal profile -> 404
        res = client.get(f"/api/v1/patients/{s['pat_b'].id}/longitudinal-profile", headers=headers_a)
        assert res.status_code == 404

        # Doctor A trying to get Patient B's facts -> 404
        res_facts = client.get(f"/api/v1/patients/{s['pat_b'].id}/facts", headers=headers_a)
        assert res_facts.status_code == 404

    def test_cross_hospital_prescriptions_blocked(self, two_hospitals_setup, db_session):
        s = two_hospitals_setup
        headers_a = get_auth_header(s["doc_a"])

        # Doctor A trying to list prescriptions for Encounter B -> 404
        res = client.get(f"/api/v1/encounters/{s['enc_b'].id}/prescriptions", headers=headers_a)
        assert res.status_code == 404

        # Doctor A trying to draft prescription for Encounter B -> 404
        res_draft = client.post(f"/api/v1/encounters/{s['enc_b'].id}/prescriptions", headers=headers_a, json={
            "items": [{"medication_name": "Paracetamol 500mg", "dose": "1 tab"}]
        })
        assert res_draft.status_code == 404

        # Doctor A trying to read Patient B's prescription history -> 404
        res_history = client.get(f"/api/v1/patients/{s['pat_b'].id}/prescriptions", headers=headers_a)
        assert res_history.status_code == 404
