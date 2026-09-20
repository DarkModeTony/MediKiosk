import pytest
import uuid
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.models.models import (
    Hospital, User, Patient, Encounter,
    DocTalkConsultation, DocTalkConsultationNote, DocTalkNotification, AuditLog
)
from app.core.security import create_access_token, hash_password
from app.database import Base, engine, SessionLocal
from app.services.doctalk_notification_service import check_and_expire_pending_requests

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
    h = Hospital(name=name or ("Hospital " + _uid()))
    db.add(h)
    db.commit()
    db.refresh(h)
    return h


def create_doctor(db, hospital_id, specialty="General Medicine",
                  availability_status="ONLINE", doctalk_enabled=True,
                  is_verified=True, role="DOCTOR", display_name=None):
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


def auth_header_for(doc: User):
    token = create_access_token({"sub": str(doc.id), "role": doc.role or "DOCTOR"})
    return {"Authorization": f"Bearer {token}"}


def create_patient_and_encounter(db, hospital_id):
    pat = Patient(
        hospital_id=hospital_id,
        demographic_data={
            "name": "Ramesh Gupta",
            "age": 52,
            "gender": "Male",
            "city": "Mumbai",
        }
    )
    db.add(pat)
    db.commit()
    db.refresh(pat)

    enc = Encounter(
        patient_id=pat.id,
        status="IN_PROGRESS",
    )
    db.add(enc)
    db.commit()
    db.refresh(enc)
    return pat, enc


# ---------------------------------------------------------------------------
# Test 1: Notification on Accept
# ---------------------------------------------------------------------------
def test_notification_on_accept(db_session):
    hosp_a = create_hospital(db_session, "Metro City Clinic")
    hosp_b = create_hospital(db_session, "Apex Heart Institute")
    dr_rahul = create_doctor(db_session, hosp_a.id, specialty="General Medicine", display_name="Dr. Rahul Verma")
    dr_priya = create_doctor(db_session, hosp_b.id, specialty="Cardiology", display_name="Dr. Priya Nair")
    pat, enc = create_patient_and_encounter(db_session, hosp_a.id)

    # 1. Dr. Rahul creates DocTalk consultation request targeting Dr. Priya
    req_payload = {
        "encounter_id": str(enc.id),
        "specialist_id": str(dr_priya.id),
        "specialty": "Cardiology",
        "reason": "Sudden onset chest discomfort with atypical ECG findings",
        "urgency": "URGENT",
        "requested_duration_minutes": 5,
    }
    create_res = client.post("/api/v1/doctalk/requests", json=req_payload, headers=auth_header_for(dr_rahul))
    assert create_res.status_code == 201
    consult_id = create_res.json()["id"]

    # 2. Verify Dr. Priya received request arrival notification
    priya_notifs = client.get("/api/v1/doctalk/notifications?unread_only=true", headers=auth_header_for(dr_priya)).json()
    assert any(n["event_type"] == "DOCTALK_REQUEST_CREATED" and n["consultation_id"] == consult_id for n in priya_notifs)

    # 3. Dr. Priya accepts consultation
    accept_res = client.post(f"/api/v1/doctalk/requests/{consult_id}/accept", headers=auth_header_for(dr_priya))
    assert accept_res.status_code == 200
    assert accept_res.json()["status"] == "ACCEPTED"

    # 4. Verify Dr. Rahul received DOCTALK_ACCEPTED notification
    rahul_notifs = client.get("/api/v1/doctalk/notifications?unread_only=true", headers=auth_header_for(dr_rahul)).json()
    accept_notif = next((n for n in rahul_notifs if n["event_type"] == "DOCTALK_ACCEPTED" and n["consultation_id"] == consult_id), None)
    assert accept_notif is not None
    assert "Priya" in accept_notif["message"] or "accepted" in accept_notif["message"]
    assert accept_notif["severity"] == "SUCCESS"
    assert accept_notif["is_read"] is False


# ---------------------------------------------------------------------------
# Test 2: Notification on Decline
# ---------------------------------------------------------------------------
def test_notification_on_decline(db_session):
    hosp_a = create_hospital(db_session)
    hosp_b = create_hospital(db_session)
    dr_rahul = create_doctor(db_session, hosp_a.id, specialty="Internal Medicine")
    dr_priya = create_doctor(db_session, hosp_b.id, specialty="Neurology")
    pat, enc = create_patient_and_encounter(db_session, hosp_a.id)

    # Request consultation
    req_payload = {
        "encounter_id": str(enc.id),
        "specialist_id": str(dr_priya.id),
        "specialty": "Neurology",
        "reason": "Acute episodic vertigo with nystagmus",
        "urgency": "ROUTINE",
        "requested_duration_minutes": 5,
    }
    res = client.post("/api/v1/doctalk/requests", json=req_payload, headers=auth_header_for(dr_rahul))
    assert res.status_code == 201
    consult_id = res.json()["id"]

    # Specialist declines
    decline_reason = "Currently performing acute thrombectomy in neuro-ICU"
    dec_res = client.post(
        f"/api/v1/doctalk/requests/{consult_id}/decline",
        json={"reason": decline_reason},
        headers=auth_header_for(dr_priya),
    )
    assert dec_res.status_code == 200
    assert dec_res.json()["status"] == "DECLINED"

    # Verify treating doctor receives DOCTALK_DECLINED notification with reason
    notifs = client.get("/api/v1/doctalk/notifications?unread_only=true", headers=auth_header_for(dr_rahul)).json()
    dec_notif = next((n for n in notifs if n["event_type"] == "DOCTALK_DECLINED" and n["consultation_id"] == consult_id), None)
    assert dec_notif is not None
    assert "declined" in dec_notif["title"].lower()
    assert decline_reason in dec_notif["message"]
    assert dec_notif["severity"] == "WARNING"


# ---------------------------------------------------------------------------
# Test 3: Notification on Cancellation
# ---------------------------------------------------------------------------
def test_notification_on_cancellation(db_session):
    hosp_a = create_hospital(db_session)
    hosp_b = create_hospital(db_session)
    dr_rahul = create_doctor(db_session, hosp_a.id, specialty="General Medicine")
    dr_priya = create_doctor(db_session, hosp_b.id, specialty="Pulmonology")
    pat, enc = create_patient_and_encounter(db_session, hosp_a.id)

    # Create request
    res = client.post(
        "/api/v1/doctalk/requests",
        json={
            "encounter_id": str(enc.id),
            "specialist_id": str(dr_priya.id),
            "specialty": "Pulmonology",
            "reason": "Refractory wheezing not responding to salbutamol nebulization",
            "urgency": "URGENT",
            "requested_duration_minutes": 3,
        },
        headers=auth_header_for(dr_rahul),
    )
    assert res.status_code == 201
    consult_id = res.json()["id"]

    # Treating doctor cancels
    cancel_res = client.post(f"/api/v1/doctalk/requests/{consult_id}/cancel", headers=auth_header_for(dr_rahul))
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "CANCELLED"

    # Specialist receives DOCTALK_CANCELLED notification
    priya_notifs = client.get("/api/v1/doctalk/notifications?unread_only=true", headers=auth_header_for(dr_priya)).json()
    cancel_notif = next((n for n in priya_notifs if n["event_type"] == "DOCTALK_CANCELLED" and n["consultation_id"] == consult_id), None)
    assert cancel_notif is not None
    assert "cancelled" in cancel_notif["title"].lower()


# ---------------------------------------------------------------------------
# Test 4: Request Expiration and Notification
# ---------------------------------------------------------------------------
def test_request_expiration_and_notification(db_session):
    hosp_a = create_hospital(db_session)
    hosp_b = create_hospital(db_session)
    dr_rahul = create_doctor(db_session, hosp_a.id, specialty="Emergency Medicine")
    dr_priya = create_doctor(db_session, hosp_b.id, specialty="Gastroenterology")
    pat, enc = create_patient_and_encounter(db_session, hosp_a.id)

    # Create request with short explicit validity
    res = client.post(
        "/api/v1/doctalk/requests",
        json={
            "encounter_id": str(enc.id),
            "specialist_id": str(dr_priya.id),
            "specialty": "Gastroenterology",
            "reason": "Suspected upper GI bleed with melena",
            "urgency": "URGENT",
            "requested_duration_minutes": 5,
            "validity_minutes": 1,
        },
        headers=auth_header_for(dr_rahul),
    )
    assert res.status_code == 201
    consult_id = uuid.UUID(res.json()["id"])

    # Simulate time lapse beyond expiration in DB
    consult = db_session.query(DocTalkConsultation).filter(DocTalkConsultation.id == consult_id).first()
    past_time = datetime.utcnow() - timedelta(minutes=20)
    consult.created_at = past_time
    consult.expires_at = datetime.utcnow() - timedelta(minutes=5)
    db_session.commit()

    # Trigger expiration sweeper
    expire_res = client.post("/api/v1/doctalk/requests/expire-pending", headers=auth_header_for(dr_rahul))
    assert expire_res.status_code == 200
    assert str(consult_id) in expire_res.json()["expired_consultation_ids"]

    # Verify status transitioned to EXPIRED
    db_session.refresh(consult)
    assert consult.status == "EXPIRED"

    # Verify treating doctor received DOCTALK_EXPIRED notification
    rahul_notifs = client.get("/api/v1/doctalk/notifications?unread_only=true", headers=auth_header_for(dr_rahul)).json()
    expired_notif = next((n for n in rahul_notifs if n["event_type"] == "DOCTALK_EXPIRED" and n["consultation_id"] == str(consult_id)), None)
    assert expired_notif is not None
    assert "expired" in expired_notif["title"].lower()

    # Verify specialist CANNOT accept an expired consultation
    late_accept_res = client.post(f"/api/v1/doctalk/requests/{consult_id}/accept", headers=auth_header_for(dr_priya))
    assert late_accept_res.status_code == 400
    assert "expired" in late_accept_res.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Test 5: Concurrent Requests & Race Condition Prevention
# ---------------------------------------------------------------------------
def test_concurrent_specialist_acceptance_race_condition(db_session):
    hosp_a = create_hospital(db_session)
    hosp_b = create_hospital(db_session)
    hosp_c = create_hospital(db_session)

    dr_rahul = create_doctor(db_session, hosp_a.id, specialty="Medicine")
    dr_amit = create_doctor(db_session, hosp_c.id, specialty="Medicine")
    dr_priya = create_doctor(db_session, hosp_b.id, specialty="Cardiology", availability_status="ONLINE")

    pat_a, enc_a = create_patient_and_encounter(db_session, hosp_a.id)
    pat_c, enc_c = create_patient_and_encounter(db_session, hosp_c.id)

    # Doctor A requests Dr. Priya
    res_a = client.post(
        "/api/v1/doctalk/requests",
        json={
            "encounter_id": str(enc_a.id),
            "specialist_id": str(dr_priya.id),
            "specialty": "Cardiology",
            "reason": "Chest pain A",
            "urgency": "URGENT",
            "requested_duration_minutes": 5,
        },
        headers=auth_header_for(dr_rahul),
    )
    assert res_a.status_code == 201
    consult_a_id = res_a.json()["id"]

    # Doctor B also requests Dr. Priya before Dr. Priya accepts Request A
    res_b = client.post(
        "/api/v1/doctalk/requests",
        json={
            "encounter_id": str(enc_c.id),
            "specialist_id": str(dr_priya.id),
            "specialty": "Cardiology",
            "reason": "Chest pain B",
            "urgency": "ROUTINE",
            "requested_duration_minutes": 3,
        },
        headers=auth_header_for(dr_amit),
    )
    assert res_b.status_code == 201
    consult_b_id = res_b.json()["id"]

    # Dr. Priya accepts Request A
    accept_a = client.post(f"/api/v1/doctalk/requests/{consult_a_id}/accept", headers=auth_header_for(dr_priya))
    assert accept_a.status_code == 200
    assert accept_a.json()["status"] == "ACCEPTED"

    # Verify specialist availability changed to BUSY in database
    db_session.refresh(dr_priya)
    assert dr_priya.availability_status == "BUSY"

    # Now, attempt by Dr. Priya to concurrently accept Request B must be blocked with 409 Conflict
    accept_b = client.post(f"/api/v1/doctalk/requests/{consult_b_id}/accept", headers=auth_header_for(dr_priya))
    assert accept_b.status_code == 409
    assert "active doctalk consultation in progress" in accept_b.json()["detail"].lower()

    # Also, any third doctor attempting to directly select Dr. Priya while BUSY receives 409 Conflict
    pat_d, enc_d = create_patient_and_encounter(db_session, hosp_a.id)
    conflict_req = client.post(
        "/api/v1/doctalk/requests",
        json={
            "encounter_id": str(enc_d.id),
            "specialist_id": str(dr_priya.id),
            "specialty": "Cardiology",
            "reason": "Another request",
            "urgency": "ROUTINE",
            "requested_duration_minutes": 3,
        },
        headers=auth_header_for(dr_rahul),
    )
    assert conflict_req.status_code == 409

    # Complete Request A
    complete_a = client.post(f"/api/v1/doctalk/requests/{consult_a_id}/complete", headers=auth_header_for(dr_priya))
    assert complete_a.status_code == 200

    # Dr. Priya's availability should now be restored to ONLINE
    db_session.refresh(dr_priya)
    assert dr_priya.availability_status == "ONLINE"

    # Now Request B can be accepted safely
    accept_b_after = client.post(f"/api/v1/doctalk/requests/{consult_b_id}/accept", headers=auth_header_for(dr_priya))
    assert accept_b_after.status_code == 200
    assert accept_b_after.json()["status"] == "ACCEPTED"


# ---------------------------------------------------------------------------
# Test 6: Stale UI State Handling
# ---------------------------------------------------------------------------
def test_stale_ui_state_handling(db_session):
    hosp_a = create_hospital(db_session)
    hosp_b = create_hospital(db_session)
    dr_rahul = create_doctor(db_session, hosp_a.id, specialty="Medicine")
    dr_priya = create_doctor(db_session, hosp_b.id, specialty="Dermatology")
    pat, enc = create_patient_and_encounter(db_session, hosp_a.id)

    # Create request
    res = client.post(
        "/api/v1/doctalk/requests",
        json={
            "encounter_id": str(enc.id),
            "specialist_id": str(dr_priya.id),
            "specialty": "Dermatology",
            "reason": "Severe generalized rash",
            "urgency": "ROUTINE",
            "requested_duration_minutes": 5,
        },
        headers=auth_header_for(dr_rahul),
    )
    consult_id = res.json()["id"]

    # Dr. Rahul cancels request
    client.post(f"/api/v1/doctalk/requests/{consult_id}/cancel", headers=auth_header_for(dr_rahul))

    # Stale UI on specialist side attempts to accept cancelled consultation
    stale_accept = client.post(f"/api/v1/doctalk/requests/{consult_id}/accept", headers=auth_header_for(dr_priya))
    assert stale_accept.status_code == 400
    assert "must be 'requested'" in stale_accept.json()["detail"].lower()

    # Stale UI on specialist side attempts to decline cancelled consultation
    stale_decline = client.post(
        f"/api/v1/doctalk/requests/{consult_id}/decline",
        json={"reason": "Busy"},
        headers=auth_header_for(dr_priya),
    )
    assert stale_decline.status_code == 400

    # Stale UI attempts to start a cancelled consultation
    stale_start = client.post(f"/api/v1/doctalk/requests/{consult_id}/start", headers=auth_header_for(dr_rahul))
    assert stale_start.status_code == 400


# ---------------------------------------------------------------------------
# Test 7: Reconnect and Notification Delivery
# ---------------------------------------------------------------------------
def test_reconnect_and_notification_delivery(db_session):
    hosp_a = create_hospital(db_session)
    dr_doc = create_doctor(db_session, hosp_a.id, specialty="Pediatrics")

    # Seed 3 notifications for dr_doc directly
    from app.services.doctalk_notification_service import create_doctalk_notification
    n1 = create_doctalk_notification(db_session, dr_doc.id, "DOCTALK_ACCEPTED", "Request Accepted", "Dr. A accepted")
    n2 = create_doctalk_notification(db_session, dr_doc.id, "DOCTALK_DECLINED", "Request Declined", "Dr. B declined", severity="WARNING")
    n3 = create_doctalk_notification(db_session, dr_doc.id, "DOCTALK_STARTED", "Session Started", "Consultation active", severity="INFO")

    # Check unread count
    count_res = client.get("/api/v1/doctalk/notifications/count", headers=auth_header_for(dr_doc))
    assert count_res.status_code == 200
    assert count_res.json()["unread_count"] >= 3

    # Mark single notification as read
    read_res = client.post(f"/api/v1/doctalk/notifications/{n1.id}/read", headers=auth_header_for(dr_doc))
    assert read_res.status_code == 200
    assert read_res.json()["is_read"] is True

    # Check count decreased by 1
    count_after = client.get("/api/v1/doctalk/notifications/count", headers=auth_header_for(dr_doc)).json()["unread_count"]
    assert count_after == count_res.json()["unread_count"] - 1

    # Mark all read
    mark_all_res = client.post("/api/v1/doctalk/notifications/read-all", headers=auth_header_for(dr_doc))
    assert mark_all_res.status_code == 200

    # Final unread count should be 0
    final_count = client.get("/api/v1/doctalk/notifications/count", headers=auth_header_for(dr_doc)).json()["unread_count"]
    assert final_count == 0

    # Retrieve all notifications (simulating fresh reconnect)
    all_notifs = client.get("/api/v1/doctalk/notifications", headers=auth_header_for(dr_doc)).json()
    assert len(all_notifs) >= 3
    assert all(n["is_read"] is True for n in all_notifs if n["id"] in (str(n1.id), str(n2.id), str(n3.id)))
