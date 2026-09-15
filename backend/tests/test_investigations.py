"""
Tests for Investigation Workflow Lifecycle (Gap 8).

Covers:
- Investigation order creation (/encounters/{id}/investigations)
- Status lifecycle: ORDERED -> COMPLETED -> REVIEWED
- Adding test results with parameter, unit, reference range, abnormal flag
- Doctor review & acknowledgement with review notes
- Order cancellation (/investigations/{id}/cancel)
- Encounter-level and patient-level investigation history
- Audit logging on order, results added, and reviewed
- Hospital isolation: cross-hospital investigation access blocked (404)
"""

import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.models.models import Hospital, User, Patient, Encounter, InvestigationOrder, InvestigationResult, AuditLog
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
def investigation_setup(db_session):
    hosp = Hospital(name="Narayana Health City")
    db_session.add(hosp)
    db_session.commit()
    db_session.refresh(hosp)

    doctor = User(
        hospital_id=hosp.id,
        role="DOCTOR",
        username=f"dr_patel_{uuid.uuid4().hex[:6]}",
        password_hash=hash_password("pass123")
    )
    db_session.add(doctor)
    db_session.commit()
    db_session.refresh(doctor)

    patient = Patient(
        hospital_id=hosp.id,
        demographic_data={"name": "Suresh Raina", "age": 38}
    )
    db_session.add(patient)
    db_session.commit()
    db_session.refresh(patient)

    encounter = Encounter(patient_id=patient.id, status="IN_PROGRESS")
    db_session.add(encounter)
    db_session.commit()
    db_session.refresh(encounter)

    return {"hosp": hosp, "doctor": doctor, "patient": patient, "encounter": encounter}

class TestInvestigationLifecycle:
    def test_full_investigation_lifecycle(self, investigation_setup, db_session):
        s = investigation_setup
        headers = get_auth_header(s["doctor"])

        # 1. Place Order: Complete Blood Count (CBC)
        order_payload = {
            "test_name": "Complete Blood Count (CBC)",
            "test_type": "LAB",
            "urgency": "URGENT",
            "clinical_notes": "Suspected bacterial infection, check WBC and platelets"
        }
        res_order = client.post(
            f"/api/v1/encounters/{s['encounter'].id}/investigations",
            headers=headers,
            json=order_payload
        )
        assert res_order.status_code == 201
        order_data = res_order.json()
        assert order_data["status"] == "ORDERED"
        assert order_data["test_name"] == "Complete Blood Count (CBC)"
        assert order_data["urgency"] == "URGENT"
        order_id = order_data["id"]

        # 2. Lab Enters Results -> Status transitions to COMPLETED
        results_payload = {
            "results": [
                {
                    "parameter_name": "Hemoglobin",
                    "value": "11.2",
                    "unit": "g/dL",
                    "reference_range": "13.5 - 17.5",
                    "abnormal_flag": "LOW",
                    "result_notes": "Mild normocytic normochromic anemia"
                },
                {
                    "parameter_name": "Total Leukocyte Count (WBC)",
                    "value": "14200",
                    "unit": "/cumm",
                    "reference_range": "4000 - 11000",
                    "abnormal_flag": "HIGH",
                    "result_notes": "Neutrophilic leukocytosis"
                },
                {
                    "parameter_name": "Platelet Count",
                    "value": "240000",
                    "unit": "/cumm",
                    "reference_range": "150000 - 450000",
                    "abnormal_flag": "NORMAL"
                }
            ]
        }
        res_res = client.post(
            f"/api/v1/investigations/{order_id}/results",
            headers=headers,
            json=results_payload
        )
        assert res_res.status_code == 200
        comp_data = res_res.json()
        assert comp_data["status"] == "COMPLETED"
        assert comp_data["completed_at"] is not None
        assert len(comp_data["results"]) == 3
        flags = [r["abnormal_flag"] for r in comp_data["results"]]
        assert "HIGH" in flags
        assert "LOW" in flags

        # 3. Doctor Reviews and Acknowledges Results -> Status transitions to REVIEWED
        review_payload = {
            "notes": "Reviewed CBC: Leucocytosis noted. Start empirical Amoxicillin-Clavulanate. Recheck in 5 days."
        }
        res_rev = client.post(
            f"/api/v1/investigations/{order_id}/review",
            headers=headers,
            json=review_payload
        )
        assert res_rev.status_code == 200
        rev_data = res_rev.json()
        assert rev_data["status"] == "REVIEWED"
        assert rev_data["reviewed_at"] is not None
        assert rev_data["reviewed_by"] == str(s["doctor"].id)
        assert "Reviewed CBC" in rev_data["clinical_notes"]

        # 4. Verify Encounter and Patient Investigation History
        enc_orders = client.get(f"/api/v1/encounters/{s['encounter'].id}/investigations", headers=headers).json()
        assert len(enc_orders) >= 1
        assert enc_orders[0]["id"] == order_id

        pat_orders = client.get(f"/api/v1/patients/{s['patient'].id}/investigations", headers=headers).json()
        assert len(pat_orders) >= 1

        # 5. Verify Audit Logs
        audits = db_session.query(AuditLog).filter(
            AuditLog.target_resource == f"investigations/{order_id}"
        ).all()
        actions = [a.action for a in audits]
        assert "INVESTIGATION_ORDERED" in actions
        assert "INVESTIGATION_RESULTS_ADDED" in actions
        assert "INVESTIGATION_REVIEWED" in actions

    def test_cancel_investigation_order(self, investigation_setup):
        s = investigation_setup
        headers = get_auth_header(s["doctor"])

        # Place order
        res_order = client.post(
            f"/api/v1/encounters/{s['encounter'].id}/investigations",
            headers=headers,
            json={"test_name": "Serum Electrolytes", "urgency": "ROUTINE"}
        )
        order_id = res_order.json()["id"]

        # Cancel
        res_cancel = client.post(f"/api/v1/investigations/{order_id}/cancel", headers=headers)
        assert res_cancel.status_code == 200
        assert res_cancel.json()["status"] == "CANCELLED"

    def test_cross_hospital_investigation_blocked(self, investigation_setup, db_session):
        s = investigation_setup
        headers = get_auth_header(s["doctor"])

        # Order in Hospital A
        res_order = client.post(
            f"/api/v1/encounters/{s['encounter'].id}/investigations",
            headers=headers,
            json={"test_name": "Chest X-Ray PA", "test_type": "RADIOLOGY"}
        )
        order_id = res_order.json()["id"]

        # Hospital B doctor
        hosp_b = Hospital(name="Hospital B")
        db_session.add(hosp_b)
        db_session.commit()
        db_session.refresh(hosp_b)

        doc_b = User(
            hospital_id=hosp_b.id,
            role="DOCTOR",
            username=f"dr_b_{uuid.uuid4().hex[:6]}",
            password_hash=hash_password("pass")
        )
        db_session.add(doc_b)
        db_session.commit()
        db_session.refresh(doc_b)
        headers_b = get_auth_header(doc_b)

        # Doctor B cannot access Hospital A's order -> 404
        res_get = client.get(f"/api/v1/investigations/{order_id}", headers=headers_b)
        assert res_get.status_code == 404

        # Doctor B cannot add results to Hospital A's order -> 404
        res_add = client.post(f"/api/v1/investigations/{order_id}/results", headers=headers_b, json={"results": []})
        assert res_add.status_code == 404
