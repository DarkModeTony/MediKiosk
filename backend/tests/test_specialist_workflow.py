import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.models.models import (
    Hospital, User, Patient, Encounter, PatientFact,
    ClinicalAssessment, RedFlag, ClinicalHistory,
    DocTalkConsultation, DocTalkConsultationNote, AuditLog
)
from app.core.security import create_access_token, hash_password
from app.database import Base, engine, SessionLocal

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _uid():
    return uuid.uuid4().hex[:6]


def create_hospital(db, name=None):
    h = Hospital(name=name or ("Test Hospital " + _uid()))
    db.add(h)
    db.commit()
    db.refresh(h)
    return h


def create_doctor(db, hospital_id, specialty="General Medicine",
                  availability_status="ONLINE", doctalk_enabled=True,
                  is_verified=True, role="DOCTOR", display_name=None):
    username = "doc_" + _uid()
    doc = User(
        hospital_id=hospital_id, role=role, username=username,
        display_name=display_name or ("Dr. " + username.capitalize()),
        specialty=specialty, qualification="MBBS, MD",
        doctalk_enabled=doctalk_enabled, availability_status=availability_status,
        is_verified=is_verified, password_hash=hash_password("password123"),
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def auth_header(user):
    token = create_access_token({
        "sub": str(user.id), "username": user.username, "role": user.role,
        "hospital_id": str(user.hospital_id) if user.hospital_id else None,
    })
    return {"Authorization": "Bearer " + token}


@pytest.fixture(scope="module")
def workflow_env(db_session):
    db = db_session
    hosp_a = create_hospital(db, "Apex Hospital Delhi " + _uid())
    hosp_b = create_hospital(db, "Fortis Cardiology Mumbai " + _uid())
    hosp_c = create_hospital(db, "Care Hospital Chennai " + _uid())

    doc_a = create_doctor(db, hosp_a.id, specialty="General Medicine", availability_status="ONLINE")
    spec_b = create_doctor(db, hosp_b.id, specialty="Cardiology", availability_status="ONLINE")
    other_doc = create_doctor(db, hosp_c.id, specialty="Neurology", availability_status="ONLINE")

    # Patient at Hospital A
    pat_a = Patient(
        hospital_id=hosp_a.id,
        demographic_data={"name": "Suresh Verma", "age": 58, "gender": "male", "city": "Delhi"}
    )
    db.add(pat_a)
    db.commit()
    db.refresh(pat_a)

    enc_a = Encounter(patient_id=pat_a.id, status="IN_PROGRESS")
    db.add(enc_a)
    db.commit()
    db.refresh(enc_a)

    # Add clinical history
    hist = ClinicalHistory(
        encounter_id=enc_a.id,
        history_data={
            "chief_complaint": "Exertional chest tightness radiating to left arm for 3 days",
            "summary": "58M with exertional angina, non-smoker, hypertensive."
        }
    )
    db.add(hist)

    # Add clinical assessment with vitals
    assessment = ClinicalAssessment(
        encounter_id=enc_a.id,
        doctor_id=doc_a.id,
        vitals_examination={
            "blood_pressure": "144/92 mmHg",
            "heart_rate": "88 bpm",
            "spo2": "97%",
            "temperature": "98.4 F"
        },
        hpi="Chest discomfort on climbing stairs, relieved by rest.",
        diagnosis=["Suspected Angina Pectoris", "Essential Hypertension"],
        clinical_plan="ECG ordered, cardiology tele-consult requested"
    )
    db.add(assessment)

    # Add facts (allergy and condition)
    fact1 = PatientFact(
        patient_id=pat_a.id,
        category="allergy",
        fact_type="medication",
        value="Penicillin - Severe Urticaria",
        source_type="clinical_intake",
        status="active"
    )
    fact2 = PatientFact(
        patient_id=pat_a.id,
        category="chronic_condition",
        fact_type="diagnosis",
        value="Hypertension (diagnosed 2019)",
        source_type="clinical_intake",
        status="active"
    )
    db.add_all([fact1, fact2])
    db.commit()

    return {
        "hosp_a": hosp_a, "hosp_b": hosp_b, "hosp_c": hosp_c,
        "doc_a": doc_a, "spec_b": spec_b, "other_doc": other_doc,
        "pat_a": pat_a, "enc_a": enc_a
    }


class TestSpecialistSideWorkflow:

    def test_incoming_requests_list_and_pre_acceptance_privacy(self, workflow_env):
        """
        1. Treating Doctor (Hosp A) creates consultation for Specialist (Hosp B).
        2. Specialist lists incoming consultations.
        3. Pre-acceptance privacy check: patient name is masked.
        """
        env = workflow_env
        create_payload = {
            "encounter_id": str(env["enc_a"].id),
            "specialty": "Cardiology",
            "specialist_id": str(env["spec_b"].id),
            "reason": "Abnormal ECG with T-wave inversion in V4-V6. Need opinion on urgent cath.",
            "urgency": "URGENT",
            "requested_duration_minutes": 5,
        }
        res_create = client.post(
            "/api/v1/doctalk/requests",
            json=create_payload,
            headers=auth_header(env["doc_a"])
        )
        assert res_create.status_code == 201
        consult_data = res_create.json()
        consult_id = consult_data["id"]

        # Specialist checks incoming requests
        res_list = client.get(
            "/api/v1/doctalk/requests/my-consultations?status=REQUESTED",
            headers=auth_header(env["spec_b"])
        )
        assert res_list.status_code == 200
        reqs = res_list.json()
        matching = [r for r in reqs if r["id"] == consult_id]
        assert len(matching) == 1
        req = matching[0]

        assert req["status"] == "REQUESTED"
        assert req["specialty"] == "Cardiology"
        assert req["urgency"] == "URGENT"
        assert req["requested_duration_minutes"] == 5
        assert req["requesting_hospital_name"] == env["hosp_a"].name
        # Pre-acceptance privacy: patient name is masked (None)
        assert req["patient_name"] is None

    def test_pre_acceptance_context_gating(self, workflow_env):
        """
        Pre-acceptance privacy guard:
        Calling GET /requests/{id}/context before acceptance returns minimized payload.
        """
        env = workflow_env
        # Create fresh consultation
        res_create = client.post(
            "/api/v1/doctalk/requests",
            json={
                "encounter_id": str(env["enc_a"].id),
                "specialty": "Cardiology",
                "specialist_id": str(env["spec_b"].id),
                "reason": "Second opinion on beta-blocker dosing.",
                "urgency": "NORMAL",
                "requested_duration_minutes": 3,
            },
            headers=auth_header(env["doc_a"])
        )
        assert res_create.status_code == 201
        consult_id = res_create.json()["id"]

        # Specialist attempts to fetch context before accepting
        res_ctx = client.get(
            f"/api/v1/doctalk/requests/{consult_id}/context",
            headers=auth_header(env["spec_b"])
        )
        assert res_ctx.status_code == 200
        data = res_ctx.json()
        assert data.get("minimized") is True
        assert "context" not in data or not data["context"]
        assert "Full clinical context is unlocked upon accepting" in data.get("message", "")

    def test_specialist_acceptance_and_context_access(self, workflow_env):
        """
        1. Specialist accepts the consultation request.
        2. Status changes to ACCEPTED.
        3. Full synthesized consultation context is now unlocked with is_external flag.
        """
        env = workflow_env
        res_create = client.post(
            "/api/v1/doctalk/requests",
            json={
                "encounter_id": str(env["enc_a"].id),
                "specialty": "Cardiology",
                "specialist_id": str(env["spec_b"].id),
                "reason": "Chest tightness review with ECG changes.",
                "urgency": "URGENT",
                "requested_duration_minutes": 5,
            },
            headers=auth_header(env["doc_a"])
        )
        assert res_create.status_code == 201
        consult_id = res_create.json()["id"]

        # Accept
        res_accept = client.post(
            f"/api/v1/doctalk/requests/{consult_id}/accept",
            headers=auth_header(env["spec_b"])
        )
        assert res_accept.status_code == 200
        acc_data = res_accept.json()
        assert acc_data["status"] == "ACCEPTED"
        assert acc_data["accepted_at"] is not None

        # Fetch context post-acceptance
        res_ctx = client.get(
            f"/api/v1/doctalk/requests/{consult_id}/context",
            headers=auth_header(env["spec_b"])
        )
        assert res_ctx.status_code == 200
        ctx_data = res_ctx.json()
        assert ctx_data.get("is_external") is True
        assert ctx_data["status"] == "ACCEPTED"
        assert "context" in ctx_data
        ctx = ctx_data["context"]

        # Verify scoped clinical data is accessible
        assert ctx["patient"]["age"] == 58
        assert ctx["patient"]["gender"] == "male"
        assert "chest tightness" in ctx["chief_complaint"].lower()
        assert ctx["vitals"]["blood_pressure"] == "144/92 mmHg"
        assert any("Penicillin" in (a if isinstance(a, str) else a.get("value", "")) for a in ctx.get("allergies", []))
        assert any("Hypertension" in (c if isinstance(c, str) else c.get("value", "")) for c in ctx.get("chronic_conditions", []))

    def test_strict_cross_hospital_isolation_maintained(self, workflow_env):
        """
        Verify that even with an active consultation, the specialist (Hosp B)
        CANNOT directly access patient records or encounters of Hospital A.
        Direct endpoints return 404.
        """
        env = workflow_env
        # Direct patient access attempt by Hosp B specialist
        res_pat = client.get(
            f"/api/v1/patients/{env['pat_a'].id}",
            headers=auth_header(env["spec_b"])
        )
        assert res_pat.status_code == 404

        # Direct encounter access attempt by Hosp B specialist
        res_enc = client.get(
            f"/api/v1/encounters/{env['enc_a'].id}",
            headers=auth_header(env["spec_b"])
        )
        assert res_enc.status_code == 404

    def test_specialist_decline_request(self, workflow_env):
        """
        Specialist declines an incoming consultation with a stated clinical/logistical reason.
        """
        env = workflow_env
        res_create = client.post(
            "/api/v1/doctalk/requests",
            json={
                "encounter_id": str(env["enc_a"].id),
                "specialty": "Cardiology",
                "specialist_id": str(env["spec_b"].id),
                "reason": "Need opinion on statin choice.",
                "urgency": "NORMAL",
                "requested_duration_minutes": 3,
            },
            headers=auth_header(env["doc_a"])
        )
        assert res_create.status_code == 201
        consult_id = res_create.json()["id"]

        # Decline
        res_dec = client.post(
            f"/api/v1/doctalk/requests/{consult_id}/decline",
            json={"reason": "Currently attending an emergency angioplasty in Cath Lab."},
            headers=auth_header(env["spec_b"])
        )
        assert res_dec.status_code == 200
        data = res_dec.json()
        assert data["status"] == "DECLINED"
        assert "emergency angioplasty" in data.get("decline_reason", "")

    def test_full_specialist_consultation_lifecycle(self, workflow_env):
        """
        Full lifecycle:
        1. Request created
        2. Specialist accepts
        3. Specialist starts consultation (status: IN_CONSULTATION)
        4. Specialist authors consultative clinical note
        5. Specialist completes consultation (status: COMPLETED)
        """
        env = workflow_env
        res_create = client.post(
            "/api/v1/doctalk/requests",
            json={
                "encounter_id": str(env["enc_a"].id),
                "specialty": "Cardiology",
                "specialist_id": str(env["spec_b"].id),
                "reason": "Review 58M with T-wave inversion for risk stratification.",
                "urgency": "URGENT",
                "requested_duration_minutes": 7,
            },
            headers=auth_header(env["doc_a"])
        )
        assert res_create.status_code == 201
        consult_id = res_create.json()["id"]

        # Accept
        res_accept = client.post(
            f"/api/v1/doctalk/requests/{consult_id}/accept",
            headers=auth_header(env["spec_b"])
        )
        assert res_accept.status_code == 200

        # Start Consultation
        res_start = client.post(
            f"/api/v1/doctalk/requests/{consult_id}/start",
            headers=auth_header(env["spec_b"])
        )
        assert res_start.status_code == 200
        assert res_start.json()["status"] == "IN_PROGRESS"
        assert res_start.json()["started_at"] is not None

        # Specialist authors consultation notes
        note_payload = {
            "note_text": "Specialist Review Notes:\nPatient presents with exertional symptoms and lateral leads repolarization abnormalities.",
            "clinical_opinion": "High probability of coronary artery disease / unstable angina given typical exertional pattern.",
            "recommendations": [
                "Immediate Troponin I and serial 12-lead ECGs",
                "Initiate Dual Antiplatelet Therapy (DAPT) if no contraindications",
                "Cardiology admission for urgent coronary angiography within 24 hours"
            ],
            "further_evaluation": "Echocardiogram to assess LV ejection fraction and regional wall motion abnormalities.",
            "follow_up": "Transfer to CCU / urgent cardiology consultation."
        }
        res_note = client.post(
            f"/api/v1/doctalk/requests/{consult_id}/notes",
            json=note_payload,
            headers=auth_header(env["spec_b"])
        )
        assert res_note.status_code == 201
        note_data = res_note.json()
        assert note_data["specialist_id"] == str(env["spec_b"].id)
        assert note_data["clinical_opinion"] == note_payload["clinical_opinion"]
        assert len(note_data["recommendations"]) == 3

        # Complete Consultation
        res_complete = client.post(
            f"/api/v1/doctalk/requests/{consult_id}/complete",
            headers=auth_header(env["spec_b"])
        )
        assert res_complete.status_code == 200
        comp_data = res_complete.json()
        assert comp_data["status"] == "COMPLETED"
        assert comp_data["completed_at"] is not None

    def test_unauthorized_parties_cannot_access_or_accept(self, workflow_env):
        """
        Other doctor from Hospital C cannot accept or view context of consultation between A & B.
        """
        env = workflow_env
        res_create = client.post(
            "/api/v1/doctalk/requests",
            json={
                "encounter_id": str(env["enc_a"].id),
                "specialty": "Cardiology",
                "specialist_id": str(env["spec_b"].id),
                "reason": "Cardiology opinion.",
                "urgency": "NORMAL",
                "requested_duration_minutes": 5,
            },
            headers=auth_header(env["doc_a"])
        )
        assert res_create.status_code == 201
        consult_id = res_create.json()["id"]

        # Other doctor tries to accept
        res_bad_accept = client.post(
            f"/api/v1/doctalk/requests/{consult_id}/accept",
            headers=auth_header(env["other_doc"])
        )
        # Designated specialist is Dr. B, so Dr. C should get 403
        assert res_bad_accept.status_code == 403

        # Other doctor tries to get context
        res_bad_ctx = client.get(
            f"/api/v1/doctalk/requests/{consult_id}/context",
            headers=auth_header(env["other_doc"])
        )
        # Not a party, gets 404
        assert res_bad_ctx.status_code == 404
