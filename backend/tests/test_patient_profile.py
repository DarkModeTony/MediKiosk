import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_kiosk_profile_unauthorized():
    # Calling profile without X-Session-Token should fail with 401
    res = client.get("/api/v1/kiosk/profile")
    assert res.status_code == 401
    assert "Missing X-Session-Token" in res.json().get("detail", "")

def test_kiosk_profile_invalid_token():
    res = client.get("/api/v1/kiosk/profile", headers={"X-Session-Token": "invalid-uuid-token"})
    assert res.status_code == 401
    assert "Invalid kiosk session token" in res.json().get("detail", "")

def test_kiosk_profile_anita_desai():
    # 1. Login Anita Desai via patient_002 alias
    session_res = client.post("/api/v1/kiosk/session", json={
        "patient_id": "patient_002",
        "language": "en"
    })
    assert session_res.status_code == 200
    token = session_res.json()["session_token"]
    assert token is not None

    # 2. Fetch Anita's profile
    prof_res = client.get("/api/v1/kiosk/profile", headers={"X-Session-Token": token})
    assert prof_res.status_code == 200
    data = prof_res.json()

    assert data["demographics"]["name"] == "Anita Desai"
    assert data["demographics"]["phone"] == "9000000002"
    assert data["demographics"]["gender"] == "Female"
    assert data["demographics"]["city"] == "Mumbai"

    # Profile summary check
    conditions = [c["condition"] for c in data["profile_summary"]["chronic_conditions"]]
    assert any("Rheumatoid Arthritis" in c for c in conditions)

    allergies = [a["substance"] for a in data["profile_summary"]["allergies"]]
    assert any("Sulfonamides" in a for a in allergies)

    meds = [m["name"] for m in data["profile_summary"]["current_medications"]]
    assert any("Methotrexate" in m for m in meds)

def test_kiosk_profile_identity_isolation():
    # Verify two different sessions access strictly their own data
    # Anita Desai
    res1 = client.post("/api/v1/kiosk/session", json={"patient_id": "patient_002", "language": "en"})
    token1 = res1.json()["session_token"]

    # Mohan Lal Verma
    res2 = client.post("/api/v1/kiosk/session", json={"patient_id": "patient_003", "language": "hi"})
    token2 = res2.json()["session_token"]

    prof1 = client.get("/api/v1/kiosk/profile", headers={"X-Session-Token": token1}).json()
    prof2 = client.get("/api/v1/kiosk/profile", headers={"X-Session-Token": token2}).json()

    assert prof1["demographics"]["name"] == "Anita Desai"
    assert prof2["demographics"]["name"] == "Mohan Lal Verma"
    assert prof1["patient_id"] != prof2["patient_id"]

def test_update_demographics_safe():
    session_res = client.post("/api/v1/kiosk/session", json={"patient_id": "patient_004", "language": "en"})
    token = session_res.json()["session_token"]

    # Update address and emergency contact
    update_res = client.put("/api/v1/kiosk/profile", headers={"X-Session-Token": token}, json={
        "address": "New Flat 4B, Chennai",
        "emergency_contact": {"name": "Karthik", "phone": "9841099999", "relation": "Spouse"}
    })
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "success"

    # Verify update persisted in profile
    prof_res = client.get("/api/v1/kiosk/profile", headers={"X-Session-Token": token})
    assert prof_res.json()["demographics"]["address"] == "New Flat 4B, Chennai"
    assert prof_res.json()["demographics"]["emergency_contact"]["phone"] == "9841099999"

def test_report_medical_change_creates_pending_fact():
    session_res = client.post("/api/v1/kiosk/session", json={"patient_id": "patient_005", "language": "gu"})
    token = session_res.json()["session_token"]

    # Report change
    rep_res = client.post("/api/v1/kiosk/profile/report-change", headers={"X-Session-Token": token}, json={
        "category": "allergy",
        "description": "I also had a severe reaction to Ibuprofen last month with facial swelling"
    })
    assert rep_res.status_code == 200
    assert rep_res.json()["status"] == "submitted_for_review"

    # Verify report appears in medical history pending reports
    hist_res = client.get("/api/v1/kiosk/medical-history", headers={"X-Session-Token": token})
    assert hist_res.status_code == 200
    history = hist_res.json()
    assert any("Ibuprofen" in r["description"] for r in history["pending_reports"])
