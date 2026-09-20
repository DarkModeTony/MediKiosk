"""
DocTalk Phase 11 — Security, Privacy & Cross-Hospital Audit Test Suite

Covers every attack vector specified in Phase 11:
- Unauthenticated access (no JWT, invalid JWT)
- Third-party hospital doctor cannot access consultations
- Wrong specialist (non-designated) cannot accept/decline
- Expired / cancelled / completed consultation lifecycle guards
- Specialist cannot access patient data outside DocTalk
- ID enumeration protection (random UUIDs, manipulated IDs)
- encounter_id filter ownership check
- Notes on pre-accept (REQUESTED) consultations blocked
- Open-specialist eligibility enforcement
- Full 7-field cross-hospital audit log verification
"""

import pytest
import uuid
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from app.main import app
from app.models.models import (
    Hospital, User, Patient, Encounter,
    DocTalkConsultation, DocTalkConsultationNote, AuditLog,
)
from app.core.security import create_access_token, hash_password
from app.database import Base, engine, SessionLocal

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def _hospital(db, name=None):
    h = Hospital(name=name or f"TestHosp-{uuid.uuid4().hex[:6]}")
    db.add(h)
    db.commit()
    db.refresh(h)
    return h


def _doctor(db, hospital_id, specialty="General Medicine", doctalk_enabled=True, is_verified=True, availability_status="AVAILABLE"):
    u = User(
        hospital_id=hospital_id,
        role="DOCTOR",
        username=f"dr_{uuid.uuid4().hex[:8]}",
        display_name=f"Dr. {uuid.uuid4().hex[:4]}",
        specialty=specialty,
        doctalk_enabled=doctalk_enabled,
        is_verified=is_verified,
        availability_status=availability_status,
        password_hash=hash_password("test"),
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def _patient(db, hospital_id):
    p = Patient(hospital_id=hospital_id, demographic_data={"name": "Test", "age": 40, "gender": "M"})
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


def _encounter(db, patient_id):
    e = Encounter(patient_id=patient_id, status="IN_PROGRESS")
    db.add(e)
    db.commit()
    db.refresh(e)
    return e


def _token(user):
    return create_access_token({
        "sub": str(user.id),
        "username": user.username,
        "role": user.role,
        "hospital_id": str(user.hospital_id) if user.hospital_id else None,
    })


def _auth(user):
    return {"Authorization": f"Bearer {_token(user)}"}


def _create_consultation(db, doctor_a, patient_a, enc_a, specialist_b, specialty="Cardiology"):
    c = DocTalkConsultation(
        requesting_doctor_id=doctor_a.id,
        requesting_hospital_id=doctor_a.hospital_id,
        specialist_id=specialist_b.id,
        specialist_hospital_id=specialist_b.hospital_id,
        patient_id=patient_a.id,
        patient_home_hospital_id=patient_a.hospital_id,
        encounter_id=enc_a.id,
        specialty=specialty,
        reason="Security test consultation",
        urgency="ROUTINE",
        requested_duration_minutes=5,
        status="REQUESTED",
        access_scope={"patient": {"age": 40, "gender": "M"}},
        expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=10),
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@pytest.fixture
def scenario(db):
    hosp_a = _hospital(db, "Apollo Security Test")
    hosp_b = _hospital(db, "Fortis Security Test")
    hosp_c = _hospital(db, "Max Security Test")
    doc_a = _doctor(db, hosp_a.id, specialty="Internal Medicine")
    spec_b = _doctor(db, hosp_b.id, specialty="Cardiology")
    doc_c = _doctor(db, hosp_c.id, specialty="Neurology")
    pat_a = _patient(db, hosp_a.id)
    enc_a = _encounter(db, pat_a.id)
    consult = _create_consultation(db, doc_a, pat_a, enc_a, spec_b)
    return {
        "hosp_a": hosp_a, "hosp_b": hosp_b, "hosp_c": hosp_c,
        "doc_a": doc_a, "spec_b": spec_b, "doc_c": doc_c,
        "pat_a": pat_a, "enc_a": enc_a, "consult": consult,
    }


class TestAuthentication:
    def test_no_jwt_specialists_returns_401(self):
        assert client.get("/api/v1/doctalk/specialists").status_code == 401

    def test_no_jwt_list_requests_returns_401(self):
        assert client.get("/api/v1/doctalk/requests").status_code == 401

    def test_no_jwt_create_request_returns_401(self):
        assert client.post("/api/v1/doctalk/requests", json={}).status_code == 401

    def test_no_jwt_accept_returns_401(self, scenario):
        cid = str(scenario["consult"].id)
        assert client.post(f"/api/v1/doctalk/requests/{cid}/accept").status_code == 401

    def test_no_jwt_context_returns_401(self, scenario):
        cid = str(scenario["consult"].id)
        assert client.get(f"/api/v1/doctalk/requests/{cid}/context").status_code == 401

    def test_no_jwt_notifications_returns_401(self):
        assert client.get("/api/v1/doctalk/notifications").status_code == 401

    def test_invalid_jwt_returns_401(self, scenario):
        bad = {"Authorization": "Bearer this.is.not.valid"}
        cid = str(scenario["consult"].id)
        assert client.get(f"/api/v1/doctalk/requests/{cid}", headers=bad).status_code == 401
        assert client.get("/api/v1/doctalk/specialists", headers=bad).status_code == 401

    def test_x_test_hospital_header_bypassed_blocked(self, scenario):
        hosp_id = str(scenario["hosp_a"].id)
        bypass_headers = {"X-Test-Hospital-Id": hosp_id}
        res = client.get("/api/v1/doctalk/specialists", headers=bypass_headers)
        assert res.status_code == 401, (
            f"CRITICAL: X-Test-Hospital-Id bypass still works on DocTalk! Got {res.status_code}"
        )


class TestThirdPartyHospitalIsolation:
    def test_third_party_cannot_view_consultation(self, scenario):
        cid = str(scenario["consult"].id)
        assert client.get(f"/api/v1/doctalk/requests/{cid}", headers=_auth(scenario["doc_c"])).status_code == 404

    def test_third_party_cannot_accept(self, scenario):
        cid = str(scenario["consult"].id)
        assert client.post(f"/api/v1/doctalk/requests/{cid}/accept", headers=_auth(scenario["doc_c"])).status_code in (403, 404)

    def test_third_party_cannot_cancel(self, scenario):
        cid = str(scenario["consult"].id)
        assert client.post(f"/api/v1/doctalk/requests/{cid}/cancel", headers=_auth(scenario["doc_c"])).status_code in (403, 404)

    def test_third_party_cannot_get_context(self, scenario):
        cid = str(scenario["consult"].id)
        assert client.get(f"/api/v1/doctalk/requests/{cid}/context", headers=_auth(scenario["doc_c"])).status_code in (403, 404)

    def test_third_party_cannot_get_notes(self, scenario):
        cid = str(scenario["consult"].id)
        assert client.get(f"/api/v1/doctalk/requests/{cid}/notes", headers=_auth(scenario["doc_c"])).status_code == 404

    def test_list_does_not_leak_cross_hospital(self, scenario):
        res = client.get("/api/v1/doctalk/requests", headers=_auth(scenario["doc_c"]))
        assert res.status_code == 200
        ids = [d["id"] for d in res.json()]
        assert str(scenario["consult"].id) not in ids, "CRITICAL: Hospital A consult visible to Hospital C doctor!"


class TestWrongSpecialist:
    def test_wrong_specialist_cannot_accept_designated(self, scenario, db):
        c = _create_consultation(db, scenario["doc_a"], scenario["pat_a"], scenario["enc_a"], scenario["spec_b"])
        res = client.post(f"/api/v1/doctalk/requests/{c.id}/accept", headers=_auth(scenario["doc_c"]))
        assert res.status_code in (403, 404)

    def test_requesting_doctor_cannot_accept_own(self, scenario):
        cid = str(scenario["consult"].id)
        res = client.post(f"/api/v1/doctalk/requests/{cid}/accept", headers=_auth(scenario["doc_a"]))
        assert res.status_code in (400, 403)


class TestSpecialistPatientIsolation:
    def test_specialist_cannot_access_patient_directly(self, scenario):
        pid = str(scenario["pat_a"].id)
        assert client.get(f"/api/v1/patients/{pid}", headers=_auth(scenario["spec_b"])).status_code == 404

    def test_specialist_cannot_access_encounter_directly(self, scenario):
        eid = str(scenario["enc_a"].id)
        assert client.get(f"/api/v1/encounters/{eid}", headers=_auth(scenario["spec_b"])).status_code == 404

    def test_specialist_cannot_access_longitudinal_profile(self, scenario):
        pid = str(scenario["pat_a"].id)
        assert client.get(f"/api/v1/patients/{pid}/longitudinal-profile", headers=_auth(scenario["spec_b"])).status_code == 404

    def test_specialist_cannot_access_prescriptions(self, scenario):
        pid = str(scenario["pat_a"].id)
        assert client.get(f"/api/v1/patients/{pid}/prescriptions", headers=_auth(scenario["spec_b"])).status_code == 404


class TestConsultationScopeRevocation:
    def _terminal(self, db, scenario, status_val):
        c = _create_consultation(db, scenario["doc_a"], scenario["pat_a"], scenario["enc_a"], scenario["spec_b"])
        c.status = status_val
        if status_val == "COMPLETED":
            c.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
        elif status_val == "CANCELLED":
            c.cancelled_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.commit()
        db.refresh(c)
        return c

    def test_specialist_context_revoked_after_completed(self, scenario, db):
        c = self._terminal(db, scenario, "COMPLETED")
        assert client.get(f"/api/v1/doctalk/requests/{c.id}/context", headers=_auth(scenario["spec_b"])).status_code == 403

    def test_specialist_context_revoked_after_cancelled(self, scenario, db):
        c = self._terminal(db, scenario, "CANCELLED")
        assert client.get(f"/api/v1/doctalk/requests/{c.id}/context", headers=_auth(scenario["spec_b"])).status_code == 403

    def test_expired_consultation_cannot_be_accepted(self, scenario, db):
        c = _create_consultation(db, scenario["doc_a"], scenario["pat_a"], scenario["enc_a"], scenario["spec_b"])
        c.expires_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=15)
        db.commit()
        assert client.post(f"/api/v1/doctalk/requests/{c.id}/accept", headers=_auth(scenario["spec_b"])).status_code == 400

    def test_cancelled_consultation_blocks_accept(self, scenario, db):
        c = self._terminal(db, scenario, "CANCELLED")
        assert client.post(f"/api/v1/doctalk/requests/{c.id}/accept", headers=_auth(scenario["spec_b"])).status_code == 400

    def test_completed_consultation_blocks_accept(self, scenario, db):
        c = self._terminal(db, scenario, "COMPLETED")
        assert client.post(f"/api/v1/doctalk/requests/{c.id}/accept", headers=_auth(scenario["spec_b"])).status_code == 400

    def test_specialist_notes_revoked_after_expired(self, scenario, db):
        c = _create_consultation(db, scenario["doc_a"], scenario["pat_a"], scenario["enc_a"], scenario["spec_b"])
        c.status = "EXPIRED"
        c.expires_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=5)
        db.commit()
        assert client.get(f"/api/v1/doctalk/requests/{c.id}/notes", headers=_auth(scenario["spec_b"])).status_code == 403

    def test_specialist_notes_revoked_after_cancelled(self, scenario, db):
        c = self._terminal(db, scenario, "CANCELLED")
        assert client.get(f"/api/v1/doctalk/requests/{c.id}/notes", headers=_auth(scenario["spec_b"])).status_code == 403

    def test_requesting_doctor_retains_notes_access_after_completed(self, scenario, db):
        c = self._terminal(db, scenario, "COMPLETED")
        assert client.get(f"/api/v1/doctalk/requests/{c.id}/notes", headers=_auth(scenario["doc_a"])).status_code == 200


class TestIdEnumerationProtection:
    def test_random_consultation_uuid_returns_404(self, scenario):
        rid = str(uuid.uuid4())
        assert client.get(f"/api/v1/doctalk/requests/{rid}", headers=_auth(scenario["doc_a"])).status_code == 404
        assert client.post(f"/api/v1/doctalk/requests/{rid}/accept", headers=_auth(scenario["spec_b"])).status_code == 404

    def test_random_patient_uuid_returns_404(self, scenario):
        assert client.get(f"/api/v1/patients/{uuid.uuid4()}", headers=_auth(scenario["doc_a"])).status_code == 404

    def test_non_uuid_consultation_id_returns_404(self, scenario):
        assert client.get("/api/v1/doctalk/requests/not-a-uuid", headers=_auth(scenario["doc_a"])).status_code == 404


class TestNoteAuthorization:
    def test_requesting_doctor_cannot_post_notes(self, scenario, db):
        c = _create_consultation(db, scenario["doc_a"], scenario["pat_a"], scenario["enc_a"], scenario["spec_b"])
        c.status = "ACCEPTED"
        c.accepted_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.commit()
        res = client.post(f"/api/v1/doctalk/requests/{c.id}/notes",
                          headers=_auth(scenario["doc_a"]),
                          json={"clinical_opinion": "Unauthorized note"})
        assert res.status_code == 403

    def test_note_on_requested_consultation_blocked(self, scenario, db):
        c = _create_consultation(db, scenario["doc_a"], scenario["pat_a"], scenario["enc_a"], scenario["spec_b"])
        res = client.post(f"/api/v1/doctalk/requests/{c.id}/notes",
                          headers=_auth(scenario["spec_b"]),
                          json={"clinical_opinion": "Pre-accept note injection"})
        assert res.status_code == 400, f"VULN-07: Note accepted on REQUESTED status! {res.status_code}"

    def test_third_party_cannot_post_notes(self, scenario, db):
        c = _create_consultation(db, scenario["doc_a"], scenario["pat_a"], scenario["enc_a"], scenario["spec_b"])
        c.status = "IN_PROGRESS"
        db.commit()
        res = client.post(f"/api/v1/doctalk/requests/{c.id}/notes",
                          headers=_auth(scenario["doc_c"]),
                          json={"clinical_opinion": "Unauthorized"})
        assert res.status_code in (403, 404)


class TestEncounterFilterOwnership:
    def test_encounter_filter_requires_ownership(self, scenario):
        eid = str(scenario["enc_a"].id)
        res = client.get(f"/api/v1/doctalk/requests?encounter_id={eid}", headers=_auth(scenario["doc_c"]))
        if res.status_code == 200:
            assert len(res.json()) == 0, "VULN-06: Doctor C enumerated Hospital A consultations via encounter filter!"
        else:
            assert res.status_code == 404


class TestOpenSpecialistEligibility:
    def test_ineligible_doctor_cannot_accept_open_consultation(self, scenario, db):
        hosp_d = _hospital(db, "Ineligible Hospital")
        ineligible = _doctor(db, hosp_d.id, specialty="Cardiology", doctalk_enabled=False, is_verified=True)
        open_consult = DocTalkConsultation(
            requesting_doctor_id=scenario["doc_a"].id,
            requesting_hospital_id=scenario["hosp_a"].id,
            patient_id=scenario["pat_a"].id,
            patient_home_hospital_id=scenario["hosp_a"].id,
            encounter_id=scenario["enc_a"].id,
            specialty="Cardiology",
            reason="Open eligibility test",
            urgency="ROUTINE",
            requested_duration_minutes=5,
            status="REQUESTED",
            access_scope={},
            expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=10),
        )
        db.add(open_consult)
        db.commit()
        db.refresh(open_consult)
        res = client.post(f"/api/v1/doctalk/requests/{open_consult.id}/accept", headers=_auth(ineligible))
        assert res.status_code in (400, 403), f"VULN-02: Ineligible doctor accepted open consult! {res.status_code}"


class TestAuditLogCompleteness:
    def test_declined_audit_contains_full_context(self, scenario, db):
        c = _create_consultation(db, scenario["doc_a"], scenario["pat_a"], scenario["enc_a"], scenario["spec_b"])
        res = client.post(f"/api/v1/doctalk/requests/{c.id}/decline",
                          headers=_auth(scenario["spec_b"]),
                          json={"reason": "Audit test"})
        assert res.status_code == 200
        db.commit()
        audit = db.query(AuditLog).filter(
            AuditLog.action == "DOCTALK_DECLINED",
            AuditLog.target_resource == f"doctalk_consultations/{c.id}",
        ).first()
        assert audit is not None
        d = audit.details
        for field in ("who", "from_hospital", "patient", "encounter", "for_consultation", "when"):
            assert field in d, f"Missing '{field}' in DECLINED audit log. Got: {list(d.keys())}"

    def test_cancelled_audit_contains_full_context(self, scenario, db):
        c = _create_consultation(db, scenario["doc_a"], scenario["pat_a"], scenario["enc_a"], scenario["spec_b"])
        res = client.post(f"/api/v1/doctalk/requests/{c.id}/cancel", headers=_auth(scenario["doc_a"]))
        assert res.status_code == 200
        db.commit()
        audit = db.query(AuditLog).filter(
            AuditLog.action == "DOCTALK_CANCELLED",
            AuditLog.target_resource == f"doctalk_consultations/{c.id}",
        ).first()
        assert audit is not None
        d = audit.details
        for field in ("who", "from_hospital", "patient", "encounter", "for_consultation", "when", "requesting_hospital"):
            assert field in d, f"Missing '{field}' in CANCELLED audit log. Got: {list(d.keys())}"
