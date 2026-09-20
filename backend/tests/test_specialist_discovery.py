import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.models.models import Hospital, User, Patient, Encounter
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
def network(db_session):
    db = db_session
    hosp_a = create_hospital(db, "Apollo Delhi " + _uid())
    hosp_b = create_hospital(db, "Fortis Mumbai " + _uid())
    hosp_c = create_hospital(db, "Max Saket " + _uid())
    doc_a       = create_doctor(db, hosp_a.id, specialty="Internal Medicine", availability_status="ONLINE")
    spec_b      = create_doctor(db, hosp_b.id, specialty="Cardiology",        availability_status="ONLINE")
    spec_c      = create_doctor(db, hosp_c.id, specialty="Neurology",         availability_status="ONLINE")
    spec_c2     = create_doctor(db, hosp_c.id, specialty="Cardiology",        availability_status="ONLINE")
    disabled    = create_doctor(db, hosp_b.id, specialty="Cardiology", doctalk_enabled=False, availability_status="ONLINE")
    unverified  = create_doctor(db, hosp_b.id, specialty="Cardiology", is_verified=False,    availability_status="ONLINE")
    busy_doc    = create_doctor(db, hosp_b.id, specialty="Cardiology", availability_status="BUSY")
    offline_doc = create_doctor(db, hosp_b.id, specialty="Cardiology", availability_status="OFFLINE")
    pat_a = Patient(hospital_id=hosp_a.id, demographic_data={"name": "IsolationPt", "age": 55})
    db.add(pat_a); db.commit(); db.refresh(pat_a)
    enc_a = Encounter(patient_id=pat_a.id, status="IN_PROGRESS")
    db.add(enc_a); db.commit(); db.refresh(enc_a)
    return dict(
        hosp_a=hosp_a, hosp_b=hosp_b, hosp_c=hosp_c,
        doc_a=doc_a, spec_b=spec_b, spec_c=spec_c, spec_c2=spec_c2,
        disabled_doc=disabled, unverified_doc=unverified,
        busy_doc=busy_doc, offline_doc=offline_doc,
        pat_a=pat_a, enc_a=enc_a,
    )


# ---------------------------------------------------------------------------
# Tests 1 & 2 — Cross-hospital discovery
# ---------------------------------------------------------------------------

class TestCrossHospitalDiscovery:
    def test_hospital_a_finds_hospital_b_specialist(self, network):
        """Test 1: Hospital A doctor can discover Hospital B Cardiology specialist."""
        n = network
        res = client.get("/api/v1/doctalk/specialists?specialty=Cardiology", headers=auth_header(n["doc_a"]))
        assert res.status_code == 200
        assert str(n["spec_b"].id) in [d["doctor_id"] for d in res.json()]

    def test_hospital_b_finds_hospital_c_specialist(self, network):
        """Test 2: Hospital B doctor can discover Hospital C Neurology specialist."""
        n = network
        res = client.get("/api/v1/doctalk/specialists?specialty=Neurology", headers=auth_header(n["spec_b"]))
        assert res.status_code == 200
        assert str(n["spec_c"].id) in [d["doctor_id"] for d in res.json()]

    def test_no_hospital_restriction_by_default(self, network):
        n = network
        res = client.get("/api/v1/doctalk/specialists", headers=auth_header(n["doc_a"]))
        assert res.status_code == 200
        assert len({d["hospital_id"] for d in res.json()}) >= 2

    def test_response_contains_no_private_fields(self, network):
        n = network
        res = client.get("/api/v1/doctalk/specialists", headers=auth_header(n["doc_a"]))
        assert res.status_code == 200
        for item in res.json():
            assert "doctor_id" in item and "specialty" in item and "availability_status" in item
            assert "password_hash" not in item and "phone" not in item


# ---------------------------------------------------------------------------
# Test 3 — Specialty filtering
# ---------------------------------------------------------------------------

class TestSpecialtyFiltering:
    def test_cardiology_filter_returns_cardiologists_only(self, network):
        n = network
        res = client.get("/api/v1/doctalk/specialists?specialty=Cardiology", headers=auth_header(n["doc_a"]))
        assert res.status_code == 200
        data = res.json()
        assert len(data) >= 1
        for item in data:
            assert "Cardiology" in item["specialty"]

    def test_neurology_filter_excludes_cardiologists(self, network):
        n = network
        res = client.get("/api/v1/doctalk/specialists?specialty=Neurology", headers=auth_header(n["doc_a"]))
        assert res.status_code == 200
        assert str(n["spec_b"].id) not in [d["doctor_id"] for d in res.json()]

    def test_partial_specialty_match(self, network):
        n = network
        res = client.get("/api/v1/doctalk/specialists?specialty=Cardio", headers=auth_header(n["doc_a"]))
        assert res.status_code == 200
        assert str(n["spec_b"].id) in [d["doctor_id"] for d in res.json()]

    def test_hospital_filter_restricts_to_hospital(self, network):
        n = network
        res = client.get("/api/v1/doctalk/specialists?hospital_id=" + str(n["hosp_b"].id), headers=auth_header(n["doc_a"]))
        assert res.status_code == 200
        assert all(d["hospital_id"] == str(n["hosp_b"].id) for d in res.json())

    def test_invalid_hospital_id_returns_400(self, network):
        n = network
        res = client.get("/api/v1/doctalk/specialists?hospital_id=not-a-uuid", headers=auth_header(n["doc_a"]))
        assert res.status_code == 400


# ---------------------------------------------------------------------------
# Test 4 — Availability filtering
# ---------------------------------------------------------------------------

class TestAvailabilityFiltering:
    def test_online_filter_returns_online_only(self, network):
        n = network
        res = client.get("/api/v1/doctalk/specialists?availability=ONLINE", headers=auth_header(n["doc_a"]))
        assert res.status_code == 200
        for item in res.json():
            assert item["availability_status"] == "ONLINE"

    def test_busy_doctor_excluded_from_online_filter(self, network):
        n = network
        res = client.get("/api/v1/doctalk/specialists?availability=ONLINE", headers=auth_header(n["doc_a"]))
        assert str(n["busy_doc"].id) not in [d["doctor_id"] for d in res.json()]

    def test_offline_doctor_excluded_from_online_filter(self, network):
        n = network
        res = client.get("/api/v1/doctalk/specialists?availability=ONLINE", headers=auth_header(n["doc_a"]))
        assert str(n["offline_doc"].id) not in [d["doctor_id"] for d in res.json()]

    def test_availability_status_values_are_valid(self, network):
        n = network
        res = client.get("/api/v1/doctalk/specialists", headers=auth_header(n["doc_a"]))
        assert res.status_code == 200
        for item in res.json():
            assert item["availability_status"] in ("ONLINE", "BUSY", "OFFLINE")


# ---------------------------------------------------------------------------
# Tests 5 & 6 — Eligibility enforcement
# ---------------------------------------------------------------------------

class TestEligibilityEnforcement:
    def test_doctalk_disabled_doctor_excluded(self, network):
        """Test 5: doctalk_enabled=False must exclude doctor."""
        n = network
        res = client.get("/api/v1/doctalk/specialists", headers=auth_header(n["doc_a"]))
        assert res.status_code == 200
        assert str(n["disabled_doc"].id) not in [d["doctor_id"] for d in res.json()]

    def test_unverified_doctor_excluded(self, network):
        """Test 6: is_verified=False must exclude doctor."""
        n = network
        res = client.get("/api/v1/doctalk/specialists", headers=auth_header(n["doc_a"]))
        assert res.status_code == 200
        assert str(n["unverified_doc"].id) not in [d["doctor_id"] for d in res.json()]

    def test_all_returned_doctors_satisfy_eligibility(self, network):
        n = network
        res = client.get("/api/v1/doctalk/specialists", headers=auth_header(n["doc_a"]))
        assert res.status_code == 200
        for item in res.json():
            assert item["is_verified"] is True
            assert item["doctalk_enabled"] is True
            assert item["specialty"] is not None
            assert item["hospital_id"]


# ---------------------------------------------------------------------------
# Test 7 — No available specialist
# ---------------------------------------------------------------------------

class TestNoAvailableSpecialist:
    def test_unknown_specialty_returns_empty_list(self, network):
        """Test 7a: Returns 200 + empty list for unknown specialty (not an error)."""
        n = network
        res = client.get("/api/v1/doctalk/specialists?specialty=QuantumSurgery", headers=auth_header(n["doc_a"]))
        assert res.status_code == 200
        assert res.json() == []

    def test_find_any_no_match_returns_found_false(self, network):
        """Test 7b: find-any returns found=False when no specialist available."""
        n = network
        res = client.get("/api/v1/doctalk/specialists/find-any?specialty=QuantumSurgery", headers=auth_header(n["doc_a"]))
        assert res.status_code == 200
        data = res.json()
        assert data["found"] is False
        assert data["specialist"] is None
        assert "QuantumSurgery" in data["message"]


# ---------------------------------------------------------------------------
# Test 8 — Unauthorized access
# ---------------------------------------------------------------------------

class TestUnauthorizedAccess:
    def test_no_token_specialists_returns_401(self, monkeypatch):
        """Test 8a: No token returns 401."""
        monkeypatch.setenv("AUTH_ENFORCE", "true")
        assert client.get("/api/v1/doctalk/specialists").status_code == 401

    def test_no_token_find_any_returns_401(self, monkeypatch):
        """Test 8b: No token on find-any returns 401."""
        monkeypatch.setenv("AUTH_ENFORCE", "true")
        assert client.get("/api/v1/doctalk/specialists/find-any?specialty=Cardiology").status_code == 401

    def test_invalid_token_returns_401(self):
        """Test 8c: Malformed/invalid token returns 401."""
        res = client.get("/api/v1/doctalk/specialists", headers={"Authorization": "Bearer bad.token.xyz"})
        assert res.status_code == 401


# ---------------------------------------------------------------------------
# Test 9 — Existing hospital isolation remains unchanged
# ---------------------------------------------------------------------------

class TestHospitalIsolationIntegrity:
    def test_specialist_cannot_access_other_hospital_patient(self, network):
        """Test 9a: DocTalk-visible specialist cannot access other hospital patients."""
        n = network
        assert client.get("/api/v1/patients/" + str(n["pat_a"].id), headers=auth_header(n["spec_b"])).status_code == 404

    def test_specialist_cannot_access_other_hospital_encounter(self, network):
        """Test 9b: DocTalk-visible specialist cannot access other hospital encounters."""
        n = network
        assert client.get("/api/v1/encounters/" + str(n["enc_a"].id), headers=auth_header(n["spec_b"])).status_code == 404

    def test_specialist_cannot_access_other_hospital_longitudinal_profile(self, network):
        """Test 9c: DocTalk-visible specialist cannot access other hospital patient profiles."""
        n = network
        assert client.get(
            "/api/v1/patients/" + str(n["pat_a"].id) + "/longitudinal-profile",
            headers=auth_header(n["spec_b"])
        ).status_code == 404


# ---------------------------------------------------------------------------
# Find-Any Specialist Endpoint
# ---------------------------------------------------------------------------

class TestFindAnySpecialist:
    def test_find_any_returns_online_eligible_specialist(self, network):
        n = network
        res = client.get("/api/v1/doctalk/specialists/find-any?specialty=Cardiology", headers=auth_header(n["doc_a"]))
        assert res.status_code == 200
        data = res.json()
        assert data["found"] is True
        s = data["specialist"]
        assert "Cardiology" in s["specialty"]
        assert s["availability_status"] == "ONLINE"
        assert s["is_verified"] is True
        assert s["doctalk_enabled"] is True

    def test_find_any_excludes_self(self, network):
        n = network
        res = client.get("/api/v1/doctalk/specialists/find-any?specialty=Cardiology", headers=auth_header(n["spec_b"]))
        assert res.status_code == 200
        data = res.json()
        if data["found"]:
            assert data["specialist"]["doctor_id"] != str(n["spec_b"].id)

    def test_find_any_is_deterministic(self, network):
        n = network
        h = auth_header(n["doc_a"])
        r1 = client.get("/api/v1/doctalk/specialists/find-any?specialty=Cardiology", headers=h)
        r2 = client.get("/api/v1/doctalk/specialists/find-any?specialty=Cardiology", headers=h)
        assert r1.status_code == r2.status_code == 200
        if r1.json()["found"] and r2.json()["found"]:
            assert r1.json()["specialist"]["doctor_id"] == r2.json()["specialist"]["doctor_id"]

    def test_find_any_requires_specialty_param(self, network):
        n = network
        assert client.get("/api/v1/doctalk/specialists/find-any", headers=auth_header(n["doc_a"])).status_code == 422
