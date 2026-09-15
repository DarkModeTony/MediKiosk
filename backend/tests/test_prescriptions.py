import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db, Base, engine
from app.models.models import Patient, Encounter, PatientLongitudinalProfile, PatientFact, Prescription, PrescriptionItem

client = TestClient(app)

@pytest.fixture
def test_setup():
    """Sets up a test patient and encounter in the database."""
    from sqlalchemy.orm import sessionmaker
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()

    # Create patient with penicillin allergy in longitudinal profile
    patient_id = uuid.uuid4()
    patient = Patient(
        id=patient_id,
        demographic_data={
            "name": "Arjun Sharma",
            "age": 34,
            "gender": "male",
            "phone": "9876543210"
        }
    )
    db.add(patient)
    db.flush()

    # Add longitudinal profile with penicillin allergy and existing metformin
    profile = PatientLongitudinalProfile(
        patient_id=patient.id,
        schema_version="1.0",
        profile={
            "demographics": {"name": "Arjun Sharma", "age": 34, "gender": "male"},
            "medical_history": {
                "allergies": [
                    {
                        "allergen": "Penicillin",
                        "reaction": "Anaphylaxis / Hives",
                        "severity": "severe",
                        "status": "active",
                        "verified": True
                    }
                ],
                "chronic_conditions": [
                    {"condition": "Type 2 Diabetes Mellitus", "status": "active"}
                ]
            },
            "medications": {
                "current": [
                    {
                        "name": "Metformin 500mg Tablet",
                        "dose": "500 mg",
                        "frequency": "Twice daily",
                        "route": "Oral",
                        "status": "active"
                    }
                ],
                "previous": []
            }
        }
    )
    db.add(profile)

    # Create encounter
    encounter_id = uuid.uuid4()
    encounter = Encounter(
        id=encounter_id,
        patient_id=patient.id,
        status="IN_PROGRESS"
    )
    db.add(encounter)
    db.commit()

    yield {
        "patient_id": str(patient_id),
        "encounter_id": str(encounter_id)
    }

    # Teardown
    try:
        db.query(PrescriptionItem).filter(PrescriptionItem.prescription_id.in_(
            db.query(Prescription.id).filter(Prescription.encounter_id == encounter_id)
        )).delete(synchronize_session=False)
        db.query(Prescription).filter(Prescription.encounter_id == encounter_id).delete(synchronize_session=False)
        db.query(PatientFact).filter(PatientFact.patient_id == patient_id).delete(synchronize_session=False)
        db.query(PatientLongitudinalProfile).filter(PatientLongitudinalProfile.patient_id == patient_id).delete(synchronize_session=False)
        db.query(Encounter).filter(Encounter.id == encounter_id).delete(synchronize_session=False)
        db.query(Patient).filter(Patient.id == patient_id).delete(synchronize_session=False)
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


def test_medicine_search_autocomplete():
    """Test fast medicine search against the Indian medicines dataset."""
    res = client.get("/api/v1/medicines/search?q=paracetamol&limit=5")
    assert res.status_code == 200
    data = res.json()
    assert "medicines" in data
    assert len(data["medicines"]) > 0
    first_med = data["medicines"][0]
    assert "name" in first_med
    assert "dosage_form" in first_med
    assert "suggested_routes" in first_med


def test_medicine_search_alias():
    """Test search with spelling alias: amoxicillin matches Amoxycillin."""
    res = client.get("/api/v1/medicines/search?q=amoxicillin&limit=5")
    assert res.status_code == 200
    data = res.json()
    assert len(data["medicines"]) > 0


def test_save_draft_prescription(test_setup):
    """Test saving a draft prescription with line items."""
    enc_id = test_setup["encounter_id"]
    pat_id = test_setup["patient_id"]

    payload = {
        "patient_id": pat_id,
        "notes": "Patient advised to maintain hydration.",
        "items": [
            {
                "medicine_id": 1,
                "medication_name": "Augmentin 625 Duo Tablet",
                "generic_name": "Amoxycillin (500mg), Clavulanic Acid (125mg)",
                "strength": "625 mg",
                "dosage_form": "Tablet",
                "dose": "1 tablet",
                "route": "Oral",
                "frequency": "Twice daily",
                "timing": "After food",
                "duration_value": 5,
                "duration_unit": "days",
                "quantity": 10,
                "indication": "Acute respiratory tract infection",
                "instructions": "Complete full course.",
                "is_prn": False
            },
            {
                "medicine_id": 37,
                "medication_name": "Paracetamol 650mg Tablet",
                "generic_name": "Paracetamol (650mg)",
                "strength": "650 mg",
                "dosage_form": "Tablet",
                "dose": "1 tablet",
                "route": "Oral",
                "frequency": "SOS / As needed",
                "timing": "After food",
                "duration_value": 3,
                "duration_unit": "days",
                "quantity": 6,
                "indication": "For fever > 100°F or severe body ache",
                "instructions": "Max 3 per day",
                "is_prn": True,
                "min_interval": "6 hours",
                "max_daily_dose": "3 tablets"
            }
        ]
    }

    res = client.post(f"/api/v1/encounters/{enc_id}/prescriptions", json=payload)
    assert res.status_code == 200
    rx = res.json()
    assert rx["status"] == "DRAFT"
    assert len(rx["items"]) == 2
    assert rx["encounter_id"] == enc_id

    # Verify allergy alert was triggered because patient is allergic to Penicillin and Augmentin contains Amoxycillin!
    assert rx["safety_check"] is not None
    alerts = rx["safety_check"]["alerts"]
    assert any(a["type"] == "ALLERGY_CONFLICT" for a in alerts)


def test_finalize_prescription_safety_block_and_override(test_setup):
    """Test finalization: requires acknowledgment if high severity allergy alert exists."""
    enc_id = test_setup["encounter_id"]
    pat_id = test_setup["patient_id"]

    # Save draft with Augmentin (conflicts with Penicillin allergy)
    payload = {
        "patient_id": pat_id,
        "items": [
            {
                "medication_name": "Augmentin 625 Duo Tablet",
                "generic_name": "Amoxycillin (500mg), Clavulanic Acid (125mg)",
                "dosage_form": "Tablet",
                "dose": "1 tablet",
                "route": "Oral",
                "frequency": "Twice daily",
                "duration_value": 5,
                "duration_unit": "days",
                "quantity": 10
            }
        ]
    }
    draft_res = client.post(f"/api/v1/encounters/{enc_id}/prescriptions", json=payload)
    rx_id = draft_res.json()["id"]

    # Attempt to finalize without acknowledgment -> should be blocked with 422
    fin_res_blocked = client.post(
        f"/api/v1/encounters/{enc_id}/prescriptions/{rx_id}/finalize",
        json={"acknowledged_safety_alerts": False}
    )
    assert fin_res_blocked.status_code == 422

    # Attempt to finalize WITH doctor acknowledgment -> should succeed
    fin_res = client.post(
        f"/api/v1/encounters/{enc_id}/prescriptions/{rx_id}/finalize",
        json={"acknowledged_safety_alerts": True, "notes": "Clinician confirmed desensitization protocol."}
    )
    assert fin_res.status_code == 200
    finalized_rx = fin_res.json()
    assert finalized_rx["status"] == "FINALIZED"
    assert finalized_rx["finalized_at"] is not None

    # Check that longitudinal profile was updated
    prof_res = client.get(f"/api/v1/patients/{pat_id}/longitudinal-profile")
    prof = prof_res.json()
    curr_meds = prof.get("medications", {}).get("current", [])
    assert any("Augmentin" in m.get("name", "") for m in curr_meds)


def test_amend_finalized_prescription(test_setup):
    """Test amending a finalized prescription creates a new editable draft and marks original as AMENDED."""
    enc_id = test_setup["encounter_id"]
    pat_id = test_setup["patient_id"]

    # 1. Draft & Finalize
    payload = {
        "patient_id": pat_id,
        "items": [
            {
                "medication_name": "Azithral 500 Tablet",
                "generic_name": "Azithromycin (500mg)",
                "dosage_form": "Tablet",
                "dose": "1 tablet",
                "route": "Oral",
                "frequency": "Once daily",
                "duration_value": 3,
                "duration_unit": "days",
                "quantity": 3
            }
        ]
    }
    draft = client.post(f"/api/v1/encounters/{enc_id}/prescriptions", json=payload).json()
    fin = client.post(
        f"/api/v1/encounters/{enc_id}/prescriptions/{draft['id']}/finalize",
        json={"acknowledged_safety_alerts": True}
    ).json()
    assert fin["status"] == "FINALIZED"

    # 2. Amend
    amend_res = client.post(f"/api/v1/encounters/{enc_id}/prescriptions/{fin['id']}/amend")
    assert amend_res.status_code == 200
    new_draft = amend_res.json()
    assert new_draft["status"] == "DRAFT"
    assert new_draft["id"] != fin["id"]
    assert len(new_draft["items"]) == 1

    # Verify all prescriptions for encounter
    all_enc_rx = client.get(f"/api/v1/encounters/{enc_id}/prescriptions").json()
    statuses = [r["status"] for r in all_enc_rx]
    assert "AMENDED" in statuses
    assert "DRAFT" in statuses
