import io
import os
import uuid
from datetime import datetime, timedelta
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.models import (
    Hospital,
    User,
    Patient,
    Encounter,
    ClinicalHistory,
    ClinicalAssessment,
    PatientFact,
    Prescription,
    PrescriptionItem,
    InvestigationOrder,
    InvestigationResult,
    Document,
    DocTalkConsultation,
    AuditLog,
)
from app.core.security import create_access_token, hash_password
from app.database import Base, engine, SessionLocal
from app.services.storage import get_document_storage

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


def create_doctor(
    db,
    hospital_id,
    specialty="General Medicine",
    availability_status="ONLINE",
    doctalk_enabled=True,
    is_verified=True,
    role="DOCTOR",
    display_name=None,
):
    username = "doc_" + _uid()
    doc = User(
        hospital_id=hospital_id,
        role=role,
        username=username,
        display_name=display_name or ("Dr. " + username.capitalize()),
        specialty=specialty,
        qualification="MBBS, MD",
        doctalk_enabled=doctalk_enabled,
        availability_status=availability_status,
        is_verified=is_verified,
        password_hash=hash_password("password123"),
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def auth_header(user):
    token = create_access_token(
        {
            "sub": str(user.id),
            "username": user.username,
            "role": user.role,
            "hospital_id": str(user.hospital_id) if user.hospital_id else None,
        }
    )
    return {"Authorization": "Bearer " + token}


@pytest.fixture(scope="module")
def sec_env(db_session):
    db = db_session
    storage = get_document_storage()

    hosp_a = create_hospital(db, "Apollo Hospital Delhi " + _uid())
    hosp_b = create_hospital(db, "Fortis Heart Mumbai " + _uid())
    hosp_c = create_hospital(db, "Max Super Saket " + _uid())

    doc_a = create_doctor(db, hosp_a.id, specialty="Internal Medicine", availability_status="ONLINE")
    spec_b = create_doctor(db, hosp_b.id, specialty="Cardiology", availability_status="ONLINE")
    spec_c = create_doctor(db, hosp_c.id, specialty="Neurology", availability_status="ONLINE")

    # Patient at Hospital A
    pat_a = Patient(
        hospital_id=hosp_a.id,
        demographic_data={
            "name": "Ramesh Gupta",
            "age": 62,
            "gender": "male",
            "phone": "+919876543210",
            "aadhaar": "1234-5678-9012",
            "city": "New Delhi",
        },
    )
    db.add(pat_a)
    db.commit()
    db.refresh(pat_a)

    enc_a = Encounter(patient_id=pat_a.id, status="IN_PROGRESS")
    db.add(enc_a)
    db.commit()
    db.refresh(enc_a)

    # Clinical History
    hist = ClinicalHistory(
        encounter_id=enc_a.id,
        history_data={
            "chief_complaint": "Acute retrosternal chest pain radiating to left jaw",
            "summary": "62M with acute coronary syndrome presentation, hypertensive, diabetic.",
            "symptoms": ["chest pain", "diaphoresis", "shortness of breath"],
        },
    )
    db.add(hist)

    # Doctor Assessment
    assessment = ClinicalAssessment(
        encounter_id=enc_a.id,
        doctor_id=doc_a.id,
        vitals_examination={
            "blood_pressure": "158/98 mmHg",
            "heart_rate": "104 bpm",
            "spo2": "94%",
            "temperature": "98.8 F",
        },
        hpi="Chest discomfort started 2 hours ago while climbing stairs.",
        diagnosis=["Suspected Non-ST Elevation Myocardial Infarction", "Hypertensive Urgency"],
        clinical_plan="Sublingual nitroglycerin given, serial troponin ordered, urgent cardiology consult.",
    )
    db.add(assessment)

    # Patient Facts (provenance tracked)
    allergy = PatientFact(
        patient_id=pat_a.id,
        category="allergy",
        fact_type="medication",
        value="Aspirin - Severe bronchospasm",
        source_type="clinical_intake",
        verified=True,
        confidence=0.95,
        status="active",
    )
    condition = PatientFact(
        patient_id=pat_a.id,
        category="chronic_condition",
        fact_type="diagnosis",
        value="Type 2 Diabetes Mellitus (since 2015)",
        source_type="doctor_assessment",
        verified=True,
        confidence=1.0,
        status="active",
    )
    db.add_all([allergy, condition])

    # Prescription
    rx = Prescription(
        patient_id=pat_a.id,
        encounter_id=enc_a.id,
        doctor_id=doc_a.id,
        status="FINALIZED",
    )
    db.add(rx)
    db.flush()
    rx_item = PrescriptionItem(
        prescription_id=rx.id,
        medication_name="Metoprolol Succinate 50mg",
        dose="50mg",
        frequency="OD",
        duration_value=30,
        duration_unit="days",
    )
    db.add(rx_item)

    # Investigation & Results
    inv = InvestigationOrder(
        encounter_id=enc_a.id,
        patient_id=pat_a.id,
        doctor_id=doc_a.id,
        test_name="Cardiac Biomarkers & ECG",
        test_type="CARDIOLOGY",
        urgency="STAT",
        status="COMPLETED",
    )
    db.add(inv)
    db.flush()
    res1 = InvestigationResult(
        order_id=inv.id,
        parameter_name="High Sensitivity Troponin I",
        value="0.14",
        unit="ng/mL",
        reference_range="< 0.04",
        abnormal_flag="HIGH",
    )
    res2 = InvestigationResult(
        order_id=inv.id,
        parameter_name="12-Lead ECG",
        value="ST depression in leads II, III, aVF",
        unit="",
        reference_range="Normal sinus rhythm",
        abnormal_flag="ABNORMAL",
    )
    db.add_all([res1, res2])

    # Uploaded Documents (Included in Consultation)
    stream = io.BytesIO(b"Simulated ECG report content: ST depression in inferior leads.")
    storage_id = storage.save_document(stream, "ecg_strip.pdf", str(pat_a.id))
    doc_shared = Document(
        encounter_id=enc_a.id,
        file_path=storage_id,
        doc_type="ECG_REPORT",
        status="COMPLETED",
    )
    db.add(doc_shared)

    # Unrelated Document (Belongs to Hospital A patient, but NOT in consultation scope)
    stream_unrel = io.BytesIO(b"Private Hospital A Financial Records.")
    storage_id_unrel = storage.save_document(stream_unrel, "private_billing.pdf", str(pat_a.id))
    doc_unrelated = Document(
        encounter_id=enc_a.id,
        file_path=storage_id_unrel,
        doc_type="BILLING_RECORD",
        status="COMPLETED",
    )
    db.add(doc_unrelated)
    db.commit()
    db.refresh(doc_shared)
    db.refresh(doc_unrelated)

    return {
        "hosp_a": hosp_a,
        "hosp_b": hosp_b,
        "hosp_c": hosp_c,
        "doc_a": doc_a,
        "spec_b": spec_b,
        "spec_c": spec_c,
        "pat_a": pat_a,
        "enc_a": enc_a,
        "doc_shared": doc_shared,
        "doc_unrelated": doc_unrelated,
    }


@pytest.fixture(autouse=True)
def clean_consultations(db_session, sec_env):
    def _cleanup():
        db_session.query(DocTalkConsultation).filter(
            DocTalkConsultation.specialist_id == sec_env["spec_b"].id,
            DocTalkConsultation.status.in_(["REQUESTED", "ACCEPTED", "IN_PROGRESS"]),
        ).update({"status": "COMPLETED"})
        spec = db_session.query(User).filter(User.id == sec_env["spec_b"].id).first()
        if spec:
            spec.availability_status = "ONLINE"
        db_session.commit()
    _cleanup()
    yield
    _cleanup()


class TestSecureConsultationContext:

    def test_critical_specialist_cannot_access_hospital_a_patient_api(self, sec_env):
        """
        CRITICAL TEST:
        Prove that Specialist B (Hospital B) CANNOT access Hospital A's patient directly
        through /patients/{id} or /encounters/{id} (returns 404).
        """
        env = sec_env
        res_pat = client.get(
            f"/api/v1/patients/{env['pat_a'].id}",
            headers=auth_header(env["spec_b"]),
        )
        assert res_pat.status_code == 404

        res_enc = client.get(
            f"/api/v1/encounters/{env['enc_a'].id}",
            headers=auth_header(env["spec_b"]),
        )
        assert res_enc.status_code == 404

        # Direct document endpoint access by external specialist is strictly blocked
        res_doc = client.get(
            f"/api/v1/documents/{env['doc_shared'].id}",
            headers=auth_header(env["spec_b"]),
        )
        assert res_doc.status_code == 404

    def test_specialist_can_access_scoped_context_after_acceptance(self, sec_env):
        """
        Specialist B accepts consultation and can access the synthesized consultation context.
        Verifies:
        - Demographic minimization (no name, phone, or aadhaar)
        - Provenance tracking (source_type, verified)
        - Vitals and investigations included
        """
        env = sec_env
        # Doctor A creates consultation with explicit sharing preferences
        create_payload = {
            "encounter_id": str(env["enc_a"].id),
            "specialty": "Cardiology",
            "specialist_id": str(env["spec_b"].id),
            "reason": "Suspected NSTEMI with elevated Troponin I. Advice on urgent angiography.",
            "urgency": "URGENT",
            "requested_duration_minutes": 5,
            "sharing_preferences": {
                "include_history": True,
                "include_vitals": True,
                "include_allergies": True,
                "include_medications": True,
                "include_conditions": True,
                "include_investigations": True,
                "include_documents": True,
                "selected_document_ids": [str(env["doc_shared"].id)],
            },
        }
        res_create = client.post(
            "/api/v1/doctalk/requests",
            json=create_payload,
            headers=auth_header(env["doc_a"]),
        )
        assert res_create.status_code == 201
        consult_id = res_create.json()["id"]

        # Specialist B accepts
        res_accept = client.post(
            f"/api/v1/doctalk/requests/{consult_id}/accept",
            headers=auth_header(env["spec_b"]),
        )
        assert res_accept.status_code == 200

        # Specialist B retrieves context
        res_ctx = client.get(
            f"/api/v1/doctalk/requests/{consult_id}/context",
            headers=auth_header(env["spec_b"]),
        )
        assert res_ctx.status_code == 200
        data = res_ctx.json()
        assert data["status"] == "ACCEPTED"
        assert data["is_external"] is True

        ctx = data["context"]
        # Demographic minimization check: age/gender present, NO phone or aadhaar
        assert ctx["patient"]["age"] == 62
        assert ctx["patient"]["gender"] == "male"
        assert "phone" not in ctx["patient"]
        assert "aadhaar" not in ctx["patient"]

        # Source traceability verification
        allergies = ctx.get("allergies", [])
        assert len(allergies) >= 1
        first_allergy = allergies[0]
        assert "Aspirin" in first_allergy["value"]
        assert first_allergy["source_type"] == "clinical_intake"
        assert first_allergy["verified"] is True

        # Investigations verification
        invs = ctx.get("investigations", [])
        assert len(invs) >= 1
        assert any(r["is_abnormal"] for inv in invs for r in inv.get("results", []))

        # Scoped document list verification
        docs = ctx.get("documents", [])
        assert len(docs) == 1
        assert docs[0]["document_id"] == str(env["doc_shared"].id)

    def test_scoped_document_streaming_and_unrelated_protection(self, sec_env):
        """
        Specialist B can access the explicitly shared document,
        but CANNOT access an unrelated document from Hospital A.
        """
        env = sec_env
        create_payload = {
            "encounter_id": str(env["enc_a"].id),
            "specialty": "Cardiology",
            "specialist_id": str(env["spec_b"].id),
            "reason": "ECG strip review.",
            "urgency": "ROUTINE",
            "requested_duration_minutes": 3,
            "sharing_preferences": {
                "include_documents": True,
                "selected_document_ids": [str(env["doc_shared"].id)],
            },
        }
        res_create = client.post(
            "/api/v1/doctalk/requests",
            json=create_payload,
            headers=auth_header(env["doc_a"]),
        )
        assert res_create.status_code == 201
        consult_id = res_create.json()["id"]

        # Accept
        client.post(f"/api/v1/doctalk/requests/{consult_id}/accept", headers=auth_header(env["spec_b"]))

        # 1. Specialist accesses explicitly authorized document
        res_doc = client.get(
            f"/api/v1/doctalk/requests/{consult_id}/documents/{env['doc_shared'].id}",
            headers=auth_header(env["spec_b"]),
        )
        assert res_doc.status_code == 200
        assert b"ST depression" in res_doc.content

        # 2. Specialist attempts to access UNRELATED document from Hospital A
        res_bad_doc = client.get(
            f"/api/v1/doctalk/requests/{consult_id}/documents/{env['doc_unrelated'].id}",
            headers=auth_header(env["spec_b"]),
        )
        assert res_bad_doc.status_code == 403
        assert "not included in consultation access scope" in res_bad_doc.json()["detail"]

    def test_access_revocation_on_cancellation(self, sec_env):
        """
        When consultation is CANCELLED, specialist loses active access (403 Forbidden).
        """
        env = sec_env
        res_create = client.post(
            "/api/v1/doctalk/requests",
            json={
                "encounter_id": str(env["enc_a"].id),
                "specialty": "Cardiology",
                "specialist_id": str(env["spec_b"].id),
                "reason": "Pre-op clearance.",
                "urgency": "ROUTINE",
                "requested_duration_minutes": 3,
            },
            headers=auth_header(env["doc_a"]),
        )
        assert res_create.status_code == 201
        consult_id = res_create.json()["id"]

        # Doctor A cancels the request
        res_cancel = client.post(
            f"/api/v1/doctalk/requests/{consult_id}/cancel",
            headers=auth_header(env["doc_a"]),
        )
        assert res_cancel.status_code == 200

        # Specialist B tries to fetch context -> 403 Forbidden
        res_ctx = client.get(
            f"/api/v1/doctalk/requests/{consult_id}/context",
            headers=auth_header(env["spec_b"]),
        )
        assert res_ctx.status_code == 403
        assert "cancelled" in res_ctx.json()["detail"].lower()

    def test_access_revocation_on_completion(self, sec_env):
        """
        When consultation is COMPLETED, specialist active context access is revoked (403 Forbidden).
        """
        env = sec_env
        res_create = client.post(
            "/api/v1/doctalk/requests",
            json={
                "encounter_id": str(env["enc_a"].id),
                "specialty": "Cardiology",
                "specialist_id": str(env["spec_b"].id),
                "reason": "Complete consultation test.",
                "urgency": "ROUTINE",
                "requested_duration_minutes": 3,
            },
            headers=auth_header(env["doc_a"]),
        )
        consult_id = res_create.json()["id"]

        # Accept -> Start -> Add note -> Complete
        client.post(f"/api/v1/doctalk/requests/{consult_id}/accept", headers=auth_header(env["spec_b"]))
        client.post(f"/api/v1/doctalk/requests/{consult_id}/start", headers=auth_header(env["spec_b"]))
        client.post(
            f"/api/v1/doctalk/requests/{consult_id}/notes",
            json={"clinical_opinion": "Patient stabilized. Discharged to ward."},
            headers=auth_header(env["spec_b"]),
        )
        res_comp = client.post(
            f"/api/v1/doctalk/requests/{consult_id}/complete",
            headers=auth_header(env["spec_b"]),
        )
        assert res_comp.status_code == 200

        # Specialist attempts to access context after completion -> 403 Forbidden
        res_ctx = client.get(
            f"/api/v1/doctalk/requests/{consult_id}/context",
            headers=auth_header(env["spec_b"]),
        )
        assert res_ctx.status_code == 403
        assert "completed" in res_ctx.json()["detail"].lower()

    def test_access_revocation_on_expiration(self, sec_env, db_session):
        """
        When access_expires_at is in the past, specialist access is revoked (403 Forbidden).
        """
        env = sec_env
        db = db_session
        res_create = client.post(
            "/api/v1/doctalk/requests",
            json={
                "encounter_id": str(env["enc_a"].id),
                "specialty": "Cardiology",
                "specialist_id": str(env["spec_b"].id),
                "reason": "Expiration test.",
                "urgency": "ROUTINE",
                "requested_duration_minutes": 3,
            },
            headers=auth_header(env["doc_a"]),
        )
        consult_id = res_create.json()["id"]
        client.post(f"/api/v1/doctalk/requests/{consult_id}/accept", headers=auth_header(env["spec_b"]))

        # Force consultation access_expires_at to 1 hour in the past
        consult = db.query(DocTalkConsultation).filter(DocTalkConsultation.id == uuid.UUID(consult_id)).first()
        consult.access_expires_at = datetime.utcnow() - timedelta(hours=1)
        db.commit()

        # Specialist B attempts to get context -> 403 Forbidden
        res_ctx = client.get(
            f"/api/v1/doctalk/requests/{consult_id}/context",
            headers=auth_header(env["spec_b"]),
        )
        assert res_ctx.status_code == 403
        assert "expired" in res_ctx.json()["detail"].lower()

    def test_wrong_specialist_and_arbitrary_ids(self, sec_env):
        """
        Specialist C (Hospital C) or an arbitrary UUID returns 404 (safe isolation).
        """
        env = sec_env
        res_create = client.post(
            "/api/v1/doctalk/requests",
            json={
                "encounter_id": str(env["enc_a"].id),
                "specialty": "Cardiology",
                "specialist_id": str(env["spec_b"].id),
                "reason": "Wrong specialist check.",
                "urgency": "ROUTINE",
                "requested_duration_minutes": 3,
            },
            headers=auth_header(env["doc_a"]),
        )
        consult_id = res_create.json()["id"]

        # Specialist C attempts access
        res_c = client.get(
            f"/api/v1/doctalk/requests/{consult_id}/context",
            headers=auth_header(env["spec_c"]),
        )
        assert res_c.status_code == 404

        # Arbitrary UUID
        res_arb = client.get(
            f"/api/v1/doctalk/requests/{uuid.uuid4()}/context",
            headers=auth_header(env["spec_b"]),
        )
        assert res_arb.status_code == 404

    def test_explicit_sharing_preference_omission(self, sec_env):
        """
        Verify that if Doctor A disables medication and document sharing,
        those fields are omitted or empty in access_scope.
        """
        env = sec_env
        create_payload = {
            "encounter_id": str(env["enc_a"].id),
            "specialty": "Cardiology",
            "specialist_id": str(env["spec_b"].id),
            "reason": "Assessment without medications sharing.",
            "urgency": "ROUTINE",
            "requested_duration_minutes": 3,
            "sharing_preferences": {
                "include_history": True,
                "include_vitals": True,
                "include_medications": False,  # Explicitly omitted!
                "include_documents": False,    # Explicitly omitted!
            },
        }
        res_create = client.post(
            "/api/v1/doctalk/requests",
            json=create_payload,
            headers=auth_header(env["doc_a"]),
        )
        assert res_create.status_code == 201
        consult_id = res_create.json()["id"]

        # Accept
        client.post(f"/api/v1/doctalk/requests/{consult_id}/accept", headers=auth_header(env["spec_b"]))

        res_ctx = client.get(
            f"/api/v1/doctalk/requests/{consult_id}/context",
            headers=auth_header(env["spec_b"]),
        )
        assert res_ctx.status_code == 200
        ctx = res_ctx.json()["context"]
        assert "active_medications" not in ctx
        assert "documents" not in ctx
        assert "vitals" in ctx
        assert "chief_complaint" in ctx
