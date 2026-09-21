import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models.models import Hospital, User, Patient, Encounter
from app.core.security import hash_password, create_access_token

client = TestClient(app)

def test_new_registration_reflects_in_doctor_queue():
    db = SessionLocal()
    try:
        # 1. Ensure Apollo Hospitals Delhi exists
        apollo = db.query(Hospital).filter(Hospital.name == "Apollo Hospitals Delhi").first()
        if not apollo:
            apollo = Hospital(name="Apollo Hospitals Delhi")
            db.add(apollo)
            db.commit()
            db.refresh(apollo)

        # 2. Ensure Dr. Sharma exists
        dr_sharma = db.query(User).filter(User.username == "dr.sharma").first()
        if not dr_sharma:
            dr_sharma = User(
                username="dr.sharma",
                password_hash=hash_password("doctor123"),
                role="DOCTOR",
                hospital_id=apollo.id
            )
            db.add(dr_sharma)
            db.commit()
            db.refresh(dr_sharma)

        token = create_access_token({"sub": str(dr_sharma.id), "username": "dr.sharma", "hospital_id": str(apollo.id)})

        # 3. Patient registers via kiosk (without passing x-hospital-id or with it)
        unique_phone = f"9{uuid.uuid4().int % 1000000000:09d}"
        reg_payload = {
            "demographic_data": {
                "name": "Live Test Patient",
                "age": 29,
                "gender": "Female",
                "phone": unique_phone
            },
            "consent": True
        }
        res = client.post("/api/v1/patients/register", json=reg_payload)
        assert res.status_code == 200, res.text
        data = res.json()
        new_patient_id = data["patient_id"]
        new_encounter_id = data["encounter_id"]
        assert data["hospital_id"] == str(apollo.id)

        # 4. Doctor queries active encounters
        queue_res = client.get("/api/v1/encounters/active", headers={"Authorization": f"Bearer {token}"})
        assert queue_res.status_code == 200, queue_res.text
        queue = queue_res.json()

        # Find the encounter in the queue
        matching = [item for item in queue if item["id"] == new_encounter_id]
        assert len(matching) == 1, f"Encounter {new_encounter_id} not found in active doctor queue"
        queue_item = matching[0]
        assert queue_item["patient_id"] == new_patient_id
        assert queue_item["name"] == "Live Test Patient"
        assert queue_item["status"] == "IN_PROGRESS"
        assert queue_item["chief_complaint"] == "New Patient Registration / General Intake"

    finally:
        db.close()
