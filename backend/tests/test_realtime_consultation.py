import json
import pytest
import uuid
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.main import app
from app.models.models import (
    Hospital, User, Patient, Encounter,
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
def realtime_env(db_session):
    db = db_session
    hosp_a = create_hospital(db, "Alpha Hospital Delhi " + _uid())
    hosp_b = create_hospital(db, "Beta Heart Institute Mumbai " + _uid())
    hosp_c = create_hospital(db, "Gamma Clinic Chennai " + _uid())

    treating_doc = create_doctor(db, hosp_a.id, specialty="General Medicine", display_name="Dr. Rahul Treating")
    specialist_doc = create_doctor(db, hosp_b.id, specialty="Cardiology", display_name="Dr. Ananya Specialist")
    unrelated_doc = create_doctor(db, hosp_c.id, specialty="Neurology", display_name="Dr. Arjun Outsider")

    patient = Patient(
        hospital_id=hosp_a.id,
        demographic_data={
            "name": "Rajesh Sharma",
            "age": 58,
            "gender": "male",
            "blood_group": "B+",
        },
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)

    encounter = Encounter(
        patient_id=patient.id,
        status="IN_PROGRESS",
    )
    db.add(encounter)
    db.commit()
    db.refresh(encounter)

    return {
        "hosp_a": hosp_a,
        "hosp_b": hosp_b,
        "hosp_c": hosp_c,
        "treating_doc": treating_doc,
        "specialist_doc": specialist_doc,
        "unrelated_doc": unrelated_doc,
        "patient": patient,
        "encounter": encounter,
    }


def create_consultation(db, env, status="ACCEPTED", duration=5):
    consult = DocTalkConsultation(
        requesting_doctor_id=env["treating_doc"].id,
        requesting_hospital_id=env["hosp_a"].id,
        specialist_id=env["specialist_doc"].id,
        specialist_hospital_id=env["hosp_b"].id,
        patient_id=env["patient"].id,
        patient_home_hospital_id=env["hosp_a"].id,
        encounter_id=env["encounter"].id,
        specialty="Cardiology",
        reason="Suspected acute coronary syndrome evaluation",
        urgency="URGENT",
        requested_duration_minutes=duration,
        status=status,
        access_expires_at=datetime.utcnow() + timedelta(hours=24),
        created_at=datetime.utcnow(),
    )
    if status in ("ACCEPTED", "IN_PROGRESS"):
        consult.accepted_at = datetime.utcnow()
    if status == "IN_PROGRESS":
        consult.started_at = datetime.utcnow()
    db.add(consult)
    db.commit()
    db.refresh(consult)
    return consult


class TestRealTimeConsultationSecurity:
    """Security tests for Room Token generation and access control."""

    def test_valid_participants_can_generate_room_tokens(self, db_session, realtime_env):
        consult = create_consultation(db_session, realtime_env, status="ACCEPTED", duration=5)

        # Treating Doctor requests token
        res_doc = client.post(
            f"/api/v1/doctalk/requests/{consult.id}/room-token",
            headers=auth_header(realtime_env["treating_doc"]),
        )
        assert res_doc.status_code == 200
        data_doc = res_doc.json()
        assert data_doc["room_id"] == str(consult.id)
        assert data_doc["role"] == "REQUESTING_DOCTOR"
        assert data_doc["peer_id"] == str(realtime_env["specialist_doc"].id)
        assert data_doc["peer_name"] == realtime_env["specialist_doc"].display_name
        assert data_doc["duration_minutes"] == 5
        assert data_doc["remaining_seconds"] > 0
        assert "room_token" in data_doc

        # Specialist requests token
        res_spec = client.post(
            f"/api/v1/doctalk/requests/{consult.id}/room-token",
            headers=auth_header(realtime_env["specialist_doc"]),
        )
        assert res_spec.status_code == 200
        data_spec = res_spec.json()
        assert data_spec["room_id"] == str(consult.id)
        assert data_spec["role"] == "SPECIALIST"
        assert data_spec["peer_id"] == str(realtime_env["treating_doc"].id)
        assert data_spec["peer_name"] == realtime_env["treating_doc"].display_name

    def test_unauthorized_third_party_doctor_blocked(self, db_session, realtime_env):
        consult = create_consultation(db_session, realtime_env, status="ACCEPTED")

        # Doctor C (unrelated) tries to request room token
        res = client.post(
            f"/api/v1/doctalk/requests/{consult.id}/room-token",
            headers=auth_header(realtime_env["unrelated_doc"]),
        )
        assert res.status_code == 404

    def test_unaccepted_consultation_blocked(self, db_session, realtime_env):
        consult = create_consultation(db_session, realtime_env, status="REQUESTED")

        res = client.post(
            f"/api/v1/doctalk/requests/{consult.id}/room-token",
            headers=auth_header(realtime_env["treating_doc"]),
        )
        assert res.status_code == 400
        assert "not yet been accepted" in res.json()["detail"].lower()

    def test_cancelled_consultation_blocked(self, db_session, realtime_env):
        consult = create_consultation(db_session, realtime_env, status="CANCELLED")

        res = client.post(
            f"/api/v1/doctalk/requests/{consult.id}/room-token",
            headers=auth_header(realtime_env["treating_doc"]),
        )
        assert res.status_code == 400
        assert "cancelled" in res.json()["detail"].lower()

    def test_declined_consultation_blocked(self, db_session, realtime_env):
        consult = create_consultation(db_session, realtime_env, status="DECLINED")

        res = client.post(
            f"/api/v1/doctalk/requests/{consult.id}/room-token",
            headers=auth_header(realtime_env["specialist_doc"]),
        )
        assert res.status_code == 400
        assert "declined" in res.json()["detail"].lower()

    def test_expired_consultation_blocked(self, db_session, realtime_env):
        consult = create_consultation(db_session, realtime_env, status="EXPIRED")

        res = client.post(
            f"/api/v1/doctalk/requests/{consult.id}/room-token",
            headers=auth_header(realtime_env["treating_doc"]),
        )
        assert res.status_code == 400
        assert "expired" in res.json()["detail"].lower()

    def test_completed_consultation_blocked(self, db_session, realtime_env):
        consult = create_consultation(db_session, realtime_env, status="COMPLETED")

        res = client.post(
            f"/api/v1/doctalk/requests/{consult.id}/room-token",
            headers=auth_header(realtime_env["specialist_doc"]),
        )
        assert res.status_code == 400
        assert "already ended" in res.json()["detail"].lower()


class TestRealTimeSignalingAndLifecycle:
    """End-to-end WebSocket signaling, timer synchronization, and completion lifecycle."""

    def test_websocket_protocol_lifecycle(self, db_session, realtime_env):
        consult = create_consultation(db_session, realtime_env, status="ACCEPTED", duration=3)

        # 1. Get room token
        doc_res = client.post(
            f"/api/v1/doctalk/requests/{consult.id}/room-token",
            headers=auth_header(realtime_env["treating_doc"]),
        )
        assert doc_res.status_code == 200
        doc_token = doc_res.json()["room_token"]

        # 2. Connect via WebSocket
        with client.websocket_connect(f"/api/v1/doctalk/ws/{consult.id}?token={doc_token}") as ws:
            # Welcome room state
            welcome = json.loads(ws.receive_text())
            assert welcome["type"] == "room_state"
            assert welcome["role"] == "REQUESTING_DOCTOR"
            assert welcome["remaining_seconds"] > 0

            # Ping-Pong timer sync
            ws.send_text(json.dumps({"type": "ping"}))
            pong = json.loads(ws.receive_text())
            assert pong["type"] == "pong"
            assert pong["remaining_seconds"] > 0

            # End consultation command
            ws.send_text(json.dumps({"type": "end_consultation"}))
            ended = json.loads(ws.receive_text())
            assert ended["type"] == "consultation_ended"
            assert ended["reason"] == "DOCTOR_ENDED"

        # 3. Verify DB status is COMPLETED
        db_session.expire_all()
        completed_consult = db_session.query(DocTalkConsultation).filter(DocTalkConsultation.id == consult.id).first()
        assert completed_consult.status == "COMPLETED"
        assert completed_consult.completed_at is not None

        # 4. Both doctors verify completed state via REST API
        resp_doc = client.get(
            f"/api/v1/doctalk/requests/{consult.id}",
            headers=auth_header(realtime_env["treating_doc"]),
        )
        assert resp_doc.status_code == 200
        assert resp_doc.json()["status"] == "COMPLETED"

        resp_spec = client.get(
            f"/api/v1/doctalk/requests/{consult.id}",
            headers=auth_header(realtime_env["specialist_doc"]),
        )
        assert resp_spec.status_code == 200
        assert resp_spec.json()["status"] == "COMPLETED"

    @pytest.mark.anyio
    async def test_session_manager_two_party_signaling_and_relay(self):
        from app.services.doctalk_session_manager import DocTalkConnectionManager
        mgr = DocTalkConnectionManager()
        consult_id = str(uuid.uuid4())

        class MockWs:
            def __init__(self):
                self.messages = []
                self.accepted = False
                self.closed = False

            async def accept(self):
                self.accepted = True

            async def send_text(self, text):
                self.messages.append(json.loads(text))

            async def close(self, code=1000, reason=""):
                self.closed = True

        ws1 = MockWs()
        ws2 = MockWs()

        # 1. Treating doctor connects
        await mgr.connect(ws1, consult_id, "user-doc-1", "REQUESTING_DOCTOR", "Dr. Rahul", 5)
        assert ws1.accepted is True
        assert len(ws1.messages) == 1
        assert ws1.messages[0]["type"] == "room_state"
        assert ws1.messages[0]["has_peer"] is False

        # 2. Specialist connects
        await mgr.connect(ws2, consult_id, "user-spec-2", "SPECIALIST", "Dr. Ananya", 5)
        assert ws2.accepted is True
        # Doctor receives peer_joined
        assert ws1.messages[1]["type"] == "peer_joined"
        assert ws1.messages[1]["peer_id"] == "user-spec-2"
        # Specialist receives room_state with has_peer: True
        assert ws2.messages[0]["type"] == "room_state"
        assert ws2.messages[0]["has_peer"] is True

        # 3. WebRTC Offer relay (Doctor -> Specialist)
        await mgr.relay_signal(consult_id, "user-doc-1", {"type": "offer", "sdp": "mock-offer-sdp"})
        assert ws2.messages[1]["type"] == "offer"
        assert ws2.messages[1]["sdp"] == "mock-offer-sdp"

        # 4. WebRTC Answer relay (Specialist -> Doctor)
        await mgr.relay_signal(consult_id, "user-spec-2", {"type": "answer", "sdp": "mock-answer-sdp"})
        assert ws1.messages[2]["type"] == "answer"
        assert ws1.messages[2]["sdp"] == "mock-answer-sdp"

        # 5. ICE Candidate relay (Specialist -> Doctor)
        await mgr.relay_signal(consult_id, "user-spec-2", {"type": "ice_candidate", "candidate": "mock-ice"})
        assert ws1.messages[3]["type"] == "ice_candidate"

        # 6. Media State relay (Doctor mutes mic)
        await mgr.relay_signal(consult_id, "user-doc-1", {"type": "media_state", "audio": False, "video": True})
        assert ws2.messages[2]["type"] == "media_state"
        assert ws2.messages[2]["audio"] is False

        # 7. Companion Chat message relay
        await mgr.relay_signal(consult_id, "user-spec-2", {"type": "chat_message", "text": "Start Aspirin 75mg PO OD"})
        assert ws1.messages[4]["type"] == "chat_message"
        assert "Aspirin" in ws1.messages[4]["text"]

        # 8. End Consultation broadcast
        await mgr.end_consultation(consult_id, ended_by_user_id="user-doc-1")
        assert ws1.messages[5]["type"] == "consultation_ended"
        assert ws2.messages[3]["type"] == "consultation_ended"

        # 9. Disconnect cleanup
        await mgr.disconnect(consult_id, "user-doc-1")
        await mgr.disconnect(consult_id, "user-spec-2")
        assert consult_id not in mgr.rooms

    def test_websocket_invalid_token_closed(self, db_session, realtime_env):
        consult = create_consultation(db_session, realtime_env, status="ACCEPTED")

        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect(f"/api/v1/doctalk/ws/{consult.id}?token=invalid-fake-token") as ws:
                ws.receive_text()

    def test_websocket_mismatched_consultation_token_closed(self, db_session, realtime_env):
        consult1 = create_consultation(db_session, realtime_env, status="ACCEPTED")
        consult2 = create_consultation(db_session, realtime_env, status="ACCEPTED")

        # Get token for consult1
        res = client.post(
            f"/api/v1/doctalk/requests/{consult1.id}/room-token",
            headers=auth_header(realtime_env["treating_doc"]),
        )
        token1 = res.json()["room_token"]

        # Try to connect to consult2 with token1
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect(f"/api/v1/doctalk/ws/{consult2.id}?token={token1}") as ws:
                ws.receive_text()

    def test_post_consultation_specialist_can_record_formal_opinion(self, db_session, realtime_env):
        consult = create_consultation(db_session, realtime_env, status="ACCEPTED", duration=3)

        # Complete consultation via REST
        comp_res = client.post(
            f"/api/v1/doctalk/requests/{consult.id}/complete",
            headers=auth_header(realtime_env["treating_doc"]),
        )
        assert comp_res.status_code == 200
        assert comp_res.json()["status"] == "COMPLETED"

        # Specialist writes clinical opinion
        note_res = client.post(
            f"/api/v1/doctalk/requests/{consult.id}/notes",
            headers=auth_header(realtime_env["specialist_doc"]),
            json={
                "clinical_opinion": "Patient exhibits signs consistent with NSTEMI. Immediate transfer to cardiac care recommended.",
                "recommendations": "Dual antiplatelet therapy and serial troponin monitoring.",
                "further_evaluation": "Coronary angiography within 24 hours.",
                "follow_up": "Check vitals every 30 minutes.",
            },
        )
        assert note_res.status_code == 201
        note_data = note_res.json()
        assert "NSTEMI" in note_data["clinical_opinion"]

        # Treating doctor can view the specialist's notes
        view_notes_res = client.get(
            f"/api/v1/doctalk/requests/{consult.id}/notes",
            headers=auth_header(realtime_env["treating_doc"]),
        )
        assert view_notes_res.status_code == 200
        notes = view_notes_res.json()
        assert len(notes) == 1
        assert "NSTEMI" in notes[0]["clinical_opinion"]
