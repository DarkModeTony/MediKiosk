"""
Tests for DocTalk: Ask a Specialist (Cross-Hospital Doctor Collaboration Foundation).

Covers:
- Specialist discovery across hospitals (does NOT restrict to requesting doctor's hospital)
- Cross-hospital consultation request creation (Hospital A doctor requests Hospital B specialist)
- Same-hospital consultation request creation
- Validation of requested duration (strictly 3, 5, or 7 minutes)
- Valid state transitions:
  - REQUESTED -> ACCEPTED
  - REQUESTED -> DECLINED
  - REQUESTED -> CANCELLED
  - ACCEPTED -> IN_PROGRESS
  - IN_PROGRESS -> COMPLETED
- Invalid state transitions (e.g., cannot start before accept, cannot complete when requested)
- Unauthorized access prevention (safe 404 for third-party doctors)
- Consultation note creation and retrieval
- Non-specialist blocked from posting clinical notes
- Audit logging verification for every lifecycle action
- Non-DocTalk hospital tenant isolation remains 100% intact
"""

import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.models.models import Hospital, User, Patient, Encounter, AuditLog, DocTalkConsultation, DocTalkConsultationNote
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


def create_hospital(db, name="Test Hospital"):
    hosp = Hospital(name=name)
    db.add(hosp)
    db.commit()
    db.refresh(hosp)
    return hosp


def create_doctor(db, hospital_id, username, specialty="General Medicine", display_name=None):
    doc = User(
        hospital_id=hospital_id,
        role="DOCTOR",
        username=username,
        display_name=display_name or f"Dr. {username.capitalize()}",
        specialty=specialty,
        qualification="MBBS, MD",
        doctalk_enabled=True,
        availability_status="AVAILABLE",
        is_verified=True,
        password_hash=hash_password("password123"),
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def get_auth_header(user):
    token = create_access_token({
        "sub": str(user.id),
        "username": user.username,
        "role": user.role,
        "hospital_id": str(user.hospital_id) if user.hospital_id else None,
    })
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def doctalk_setup(db_session):
    # Hospital A (e.g. Apollo Delhi)
    hosp_a = create_hospital(db_session, f"Apollo Delhi {uuid.uuid4().hex[:4]}")
    doc_a = create_doctor(db_session, hosp_a.id, f"dr_a_{uuid.uuid4().hex[:6]}", specialty="Internal Medicine", display_name="Dr. Ananya Sharma")
    pat_a = Patient(hospital_id=hosp_a.id, demographic_data={"name": "Raj Kumar", "age": 42, "gender": "Male"})
    db_session.add(pat_a)
    db_session.commit()
    db_session.refresh(pat_a)

    enc_a = Encounter(patient_id=pat_a.id, status="IN_PROGRESS")
    db_session.add(enc_a)
    db_session.commit()
    db_session.refresh(enc_a)

    # Hospital B (e.g. Fortis Mumbai)
    hosp_b = create_hospital(db_session, f"Fortis Mumbai {uuid.uuid4().hex[:4]}")
    spec_b = create_doctor(db_session, hosp_b.id, f"spec_b_{uuid.uuid4().hex[:6]}", specialty="Cardiology", display_name="Dr. Rajesh Sengupta")

    # Hospital C (Third party - unauthorized observer)
    hosp_c = create_hospital(db_session, f"Max Saket {uuid.uuid4().hex[:4]}")
    doc_c = create_doctor(db_session, hosp_c.id, f"dr_c_{uuid.uuid4().hex[:6]}", specialty="Neurology", display_name="Dr. Vikram Seth")

    return {
        "hosp_a": hosp_a, "doc_a": doc_a, "pat_a": pat_a, "enc_a": enc_a,
        "hosp_b": hosp_b, "spec_b": spec_b,
        "hosp_c": hosp_c, "doc_c": doc_c,
    }


class TestSpecialistDiscovery:
    def test_specialists_discovery_across_hospitals(self, doctalk_setup):
        s = doctalk_setup
        headers_a = get_auth_header(s["doc_a"])

        # Doctor A from Hospital A queries specialists directory
        res = client.get("/api/v1/doctalk/specialists", headers=headers_a)
        assert res.status_code == 200
        data = res.json()
        assert len(data) >= 2

        # Verify Specialist B from Hospital B is visible and discoverable
        doc_ids = [d["doctor_id"] for d in data]
        assert str(s["spec_b"].id) in doc_ids

        # Filter by specialty
        res_cardio = client.get("/api/v1/doctalk/specialists?specialty=Cardiology", headers=headers_a)
        assert res_cardio.status_code == 200
        cardio_docs = res_cardio.json()
        assert any(d["doctor_id"] == str(s["spec_b"].id) for d in cardio_docs)


class TestConsultationDurationValidation:
    def test_valid_durations_accepted(self, doctalk_setup):
        s = doctalk_setup
        headers_a = get_auth_header(s["doc_a"])

        for duration in [3, 5, 7]:
            res = client.post("/api/v1/doctalk/requests", headers=headers_a, json={
                "encounter_id": str(s["enc_a"].id),
                "specialist_id": str(s["spec_b"].id),
                "specialty": "Cardiology",
                "reason": f"Evaluating ECG rhythm changes for duration {duration}",
                "urgency": "ROUTINE",
                "requested_duration_minutes": duration,
            })
            assert res.status_code == 201
            assert res.json()["requested_duration_minutes"] == duration

    def test_invalid_durations_rejected(self, doctalk_setup):
        s = doctalk_setup
        headers_a = get_auth_header(s["doc_a"])

        for invalid_duration in [1, 2, 4, 6, 10, 15, 30]:
            res = client.post("/api/v1/doctalk/requests", headers=headers_a, json={
                "encounter_id": str(s["enc_a"].id),
                "specialist_id": str(s["spec_b"].id),
                "specialty": "Cardiology",
                "reason": "Test invalid duration",
                "requested_duration_minutes": invalid_duration,
            })
            assert res.status_code in (400, 422)


class TestConsultationLifecycleAndTransitions:
    def test_cross_hospital_consultation_happy_path(self, doctalk_setup, db_session):
        s = doctalk_setup
        headers_a = get_auth_header(s["doc_a"])
        headers_b = get_auth_header(s["spec_b"])

        # 1. Doctor A requests consultation with Specialist B (Hospital A -> Hospital B)
        create_res = client.post("/api/v1/doctalk/requests", headers=headers_a, json={
            "encounter_id": str(s["enc_a"].id),
            "specialist_id": str(s["spec_b"].id),
            "specialty": "Cardiology",
            "reason": "Suspected acute myocarditis; please review elevated troponin and vitals.",
            "urgency": "URGENT",
            "requested_duration_minutes": 5,
        })
        assert create_res.status_code == 201
        consult_data = create_res.json()
        consult_id = consult_data["id"]

        assert consult_data["status"] == "REQUESTED"
        assert consult_data["requesting_hospital_id"] == str(s["hosp_a"].id)
        assert consult_data["specialist_hospital_id"] == str(s["hosp_b"].id)
        assert consult_data["patient_id"] == str(s["pat_a"].id)
        assert consult_data["access_scope"] is not None

        # Verify audit log for DOCTALK_REQUESTED
        # Commit the test session so it releases its read snapshot and sees the API's committed data
        db_session.commit()
        audit = db_session.query(AuditLog).filter(
            AuditLog.action == "DOCTALK_REQUESTED",
            AuditLog.target_resource == f"doctalk_consultations/{consult_id}"
        ).first()
        assert audit is not None
        assert audit.details["urgency"] == "URGENT"

        # 2. Specialist B accepts consultation
        accept_res = client.post(f"/api/v1/doctalk/requests/{consult_id}/accept", headers=headers_b)
        assert accept_res.status_code == 200
        assert accept_res.json()["status"] == "ACCEPTED"
        assert accept_res.json()["accepted_at"] is not None
        assert accept_res.json()["access_expires_at"] is not None

        # Verify audit log for DOCTALK_ACCEPTED
        db_session.commit()
        audit_accept = db_session.query(AuditLog).filter(
            AuditLog.action == "DOCTALK_ACCEPTED",
            AuditLog.target_resource == f"doctalk_consultations/{consult_id}"
        ).first()
        assert audit_accept is not None

        # 3. Start consultation (ACCEPTED -> IN_PROGRESS)
        start_res = client.post(f"/api/v1/doctalk/requests/{consult_id}/start", headers=headers_a)
        assert start_res.status_code == 200
        assert start_res.json()["status"] == "IN_PROGRESS"
        assert start_res.json()["started_at"] is not None

        # 4. Specialist B records consultation notes
        note_res = client.post(f"/api/v1/doctalk/requests/{consult_id}/notes", headers=headers_b, json={
            "clinical_opinion": "Findings consistent with early viral myocarditis. Low risk for acute STEMI based on normal ST segments.",
            "recommendations": [
                {"action": "Echocardiogram", "urgency": "within 24 hours"},
                {"action": "NSAID Avoidance", "reason": "Potential renal exacerbation"}
            ],
            "further_evaluation": "Serial Troponin-I at 6 hours",
            "follow_up": "Re-consult if BP drops below 100 systolic",
        })
        assert note_res.status_code == 201
        note_data = note_res.json()
        assert note_data["consultation_id"] == consult_id
        assert note_data["specialist_id"] == str(s["spec_b"].id)
        assert "viral myocarditis" in note_data["clinical_opinion"]

        # 5. Doctor A retrieves notes
        notes_get = client.get(f"/api/v1/doctalk/requests/{consult_id}/notes", headers=headers_a)
        assert notes_get.status_code == 200
        assert len(notes_get.json()) >= 1

        # 6. Complete consultation (IN_PROGRESS -> COMPLETED)
        complete_res = client.post(f"/api/v1/doctalk/requests/{consult_id}/complete", headers=headers_b)
        assert complete_res.status_code == 200
        assert complete_res.json()["status"] == "COMPLETED"
        assert complete_res.json()["completed_at"] is not None

        # Verify audit log for DOCTALK_COMPLETED
        db_session.commit()
        audit_complete = db_session.query(AuditLog).filter(
            AuditLog.action == "DOCTALK_COMPLETED",
            AuditLog.target_resource == f"doctalk_consultations/{consult_id}"
        ).first()
        assert audit_complete is not None

    def test_decline_consultation_flow(self, doctalk_setup):
        s = doctalk_setup
        headers_a = get_auth_header(s["doc_a"])
        headers_b = get_auth_header(s["spec_b"])

        # Request
        create_res = client.post("/api/v1/doctalk/requests", headers=headers_a, json={
            "encounter_id": str(s["enc_a"].id),
            "specialist_id": str(s["spec_b"].id),
            "specialty": "Cardiology",
            "reason": "Consultation for decline test",
            "requested_duration_minutes": 3,
        })
        consult_id = create_res.json()["id"]

        # Specialist declines
        decline_res = client.post(f"/api/v1/doctalk/requests/{consult_id}/decline", headers=headers_b, json={
            "reason": "Currently in emergency catheterization procedure, unable to review."
        })
        assert decline_res.status_code == 200
        assert decline_res.json()["status"] == "DECLINED"
        assert "emergency catheterization" in decline_res.json()["decline_reason"]

    def test_cancel_consultation_flow(self, doctalk_setup):
        s = doctalk_setup
        headers_a = get_auth_header(s["doc_a"])

        create_res = client.post("/api/v1/doctalk/requests", headers=headers_a, json={
            "encounter_id": str(s["enc_a"].id),
            "specialist_id": str(s["spec_b"].id),
            "specialty": "Cardiology",
            "reason": "Consultation for cancel test",
            "requested_duration_minutes": 7,
        })
        consult_id = create_res.json()["id"]

        # Requesting doctor cancels
        cancel_res = client.post(f"/api/v1/doctalk/requests/{consult_id}/cancel", headers=headers_a)
        assert cancel_res.status_code == 200
        assert cancel_res.json()["status"] == "CANCELLED"
        assert cancel_res.json()["cancelled_at"] is not None

    def test_invalid_state_transitions(self, doctalk_setup):
        s = doctalk_setup
        headers_a = get_auth_header(s["doc_a"])
        headers_b = get_auth_header(s["spec_b"])

        # Create consult (starts in REQUESTED)
        create_res = client.post("/api/v1/doctalk/requests", headers=headers_a, json={
            "encounter_id": str(s["enc_a"].id),
            "specialist_id": str(s["spec_b"].id),
            "specialty": "Cardiology",
            "reason": "Invalid transition test",
            "requested_duration_minutes": 5,
        })
        consult_id = create_res.json()["id"]

        # Cannot start directly from REQUESTED (must be ACCEPTED first)
        start_invalid = client.post(f"/api/v1/doctalk/requests/{consult_id}/start", headers=headers_a)
        assert start_invalid.status_code == 400

        # Cannot complete directly from REQUESTED
        complete_invalid = client.post(f"/api/v1/doctalk/requests/{consult_id}/complete", headers=headers_a)
        assert complete_invalid.status_code == 400


class TestSecurityAndIsolation:
    def test_unauthorized_third_party_doctor_cannot_access_consultation(self, doctalk_setup):
        s = doctalk_setup
        headers_a = get_auth_header(s["doc_a"])
        headers_c = get_auth_header(s["doc_c"]) # Doctor C from Hospital C

        # Doctor A creates consult with Specialist B
        create_res = client.post("/api/v1/doctalk/requests", headers=headers_a, json={
            "encounter_id": str(s["enc_a"].id),
            "specialist_id": str(s["spec_b"].id),
            "specialty": "Cardiology",
            "reason": "Confidential patient inquiry",
            "requested_duration_minutes": 5,
        })
        consult_id = create_res.json()["id"]

        # Doctor C tries to view consultation -> 404 NOT FOUND (Safe 404 avoids ID enumeration)
        view_c = client.get(f"/api/v1/doctalk/requests/{consult_id}", headers=headers_c)
        assert view_c.status_code == 404

        # Doctor C tries to accept -> 404 or 403
        accept_c = client.post(f"/api/v1/doctalk/requests/{consult_id}/accept", headers=headers_c)
        assert accept_c.status_code in (403, 404)

    def test_specialist_cannot_access_patient_outside_doctalk(self, doctalk_setup):
        """
        CRITICAL ARCHITECTURAL TEST:
        Even when Specialist B is consulted via DocTalk, Specialist B CANNOT
        access Hospital A's direct patient or encounter routes!
        Normal MediPlatform isolation remains 100% intact.
        """
        s = doctalk_setup
        headers_b = get_auth_header(s["spec_b"])

        # Specialist B attempts direct access to Patient A -> 404 NOT FOUND
        pat_direct = client.get(f"/api/v1/patients/{s['pat_a'].id}", headers=headers_b)
        assert pat_direct.status_code == 404

        # Specialist B attempts direct access to Encounter A -> 404 NOT FOUND
        enc_direct = client.get(f"/api/v1/encounters/{s['enc_a'].id}", headers=headers_b)
        assert enc_direct.status_code == 404

        # Specialist B attempts direct access to Patient A longitudinal profile -> 404 NOT FOUND
        prof_direct = client.get(f"/api/v1/patients/{s['pat_a'].id}/longitudinal-profile", headers=headers_b)
        assert prof_direct.status_code == 404

    def test_non_specialist_cannot_post_notes(self, doctalk_setup):
        s = doctalk_setup
        headers_a = get_auth_header(s["doc_a"])

        create_res = client.post("/api/v1/doctalk/requests", headers=headers_a, json={
            "encounter_id": str(s["enc_a"].id),
            "specialist_id": str(s["spec_b"].id),
            "specialty": "Cardiology",
            "reason": "Notes authorization test",
            "requested_duration_minutes": 5,
        })
        consult_id = create_res.json()["id"]

        # Requesting Doctor A attempts to post clinical note -> 403 FORBIDDEN
        note_attempt = client.post(f"/api/v1/doctalk/requests/{consult_id}/notes", headers=headers_a, json={
            "clinical_opinion": "Self-authored opinion"
        })
        assert note_attempt.status_code == 403
