import pytest
import uuid
import time
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_new_patient_summary_isolation():
    """
    CRITICAL ISOLATION TEST:
    A newly registered patient with no previous medical history must NEVER receive
    another patient's (e.g., Raj Kumar's) clinical data, diagnoses, or medications in their summary.
    """
    unique_phone = f"98{int(time.time()) % 100000000:08d}"
    
    # 1. Register a new patient
    reg_res = client.post("/api/v1/patients/register", json={
        "demographic_data": {
            "name": "Pooja Sharma",
            "date_of_birth": "1995-04-12",
            "gender": "Female",
            "language": "en",
            "mobile_number": unique_phone
        },
        "consent": True
    })
    assert reg_res.status_code == 200, reg_res.text
    reg_data = reg_res.json()
    new_patient_id = reg_data["patient_id"]
    new_encounter_id = reg_data.get("encounter_id")
    assert new_patient_id is not None
    assert new_encounter_id is not None

    # 2. Create a kiosk session for this new patient
    session_res = client.post("/api/v1/kiosk/session", json={
        "patient_id": new_patient_id,
        "language": "en"
    })
    assert session_res.status_code == 200, session_res.text
    session_data = session_res.json()
    session_token = session_data["session_token"]
    assert session_data.get("encounter_id") == new_encounter_id

    # 3. Retrieve summary via session-authenticated endpoint
    summary_res = client.get("/api/v1/kiosk/summary", headers={
        "X-Session-Token": session_token
    })
    assert summary_res.status_code == 200, summary_res.text
    summary_json = summary_res.json()
    
    assert summary_json["patient_id"] == new_patient_id
    assert summary_json["encounter_id"] == new_encounter_id

    # 4. Check contents of the summary draft
    latest_version = summary_json.get("latest_version") or {}
    sections = latest_version.get("structured_sections", [])
    
    # Combine all section content
    combined_content = " ".join([s.get("content", "") for s in sections])
    combined_titles = " ".join([s.get("title", "") for s in sections])

    # MUST NOT contain Raj Kumar's data
    assert "Raj Kumar" not in combined_content
    assert "Type 2 Diabetes" not in combined_content
    assert "Appendectomy" not in combined_content
    assert "148/92" not in combined_content
    assert "Metformin" not in combined_content
    assert "Amlodipine" not in combined_content
    assert "sum_raj_999" != summary_json.get("summary_id")


def test_cross_patient_summary_isolation():
    """
    Ensure Patient A cannot access Patient B's summary data,
    and summaries generated for Patient A do not leak into Patient B.
    """
    phone_a = f"97{int(time.time() * 10) % 100000000:08d}"
    phone_b = f"96{int(time.time() * 10 + 7) % 100000000:08d}"

    # Register Patient A
    res_a = client.post("/api/v1/patients/register", json={
        "demographic_data": {"name": "Patient Alpha", "gender": "Male", "language": "en", "mobile_number": phone_a},
        "consent": True
    })
    assert res_a.status_code == 200
    pat_a_id = res_a.json()["patient_id"]
    enc_a_id = res_a.json()["encounter_id"]

    # Register Patient B
    res_b = client.post("/api/v1/patients/register", json={
        "demographic_data": {"name": "Patient Beta", "gender": "Female", "language": "en", "mobile_number": phone_b},
        "consent": True
    })
    assert res_b.status_code == 200
    pat_b_id = res_b.json()["patient_id"]
    enc_b_id = res_b.json()["encounter_id"]

    assert pat_a_id != pat_b_id
    assert enc_a_id != enc_b_id

    # Sessions
    token_a = client.post("/api/v1/kiosk/session", json={"patient_id": pat_a_id, "language": "en"}).json()["session_token"]
    token_b = client.post("/api/v1/kiosk/session", json={"patient_id": pat_b_id, "language": "en"}).json()["session_token"]

    summary_a = client.get("/api/v1/kiosk/summary", headers={"X-Session-Token": token_a}).json()
    summary_b = client.get("/api/v1/kiosk/summary", headers={"X-Session-Token": token_b}).json()

    assert summary_a["patient_id"] == pat_a_id
    assert summary_a["encounter_id"] == enc_a_id
    assert summary_b["patient_id"] == pat_b_id
    assert summary_b["encounter_id"] == enc_b_id
    assert summary_a["summary_id"] != summary_b["summary_id"]


def test_kiosk_generate_summary_endpoint():
    """
    Test explicitly triggering summary generation via POST /api/v1/kiosk/summary/generate
    """
    phone = f"95{int(time.time() * 10 + 3) % 100000000:08d}"
    reg_res = client.post("/api/v1/patients/register", json={
        "demographic_data": {"name": "Patient Gamma", "gender": "Other", "language": "en", "mobile_number": phone},
        "consent": True
    })
    pat_id = reg_res.json()["patient_id"]
    enc_id = reg_res.json()["encounter_id"]

    token = client.post("/api/v1/kiosk/session", json={"patient_id": pat_id, "language": "en"}).json()["session_token"]

    gen_res = client.post("/api/v1/kiosk/summary/generate", headers={"X-Session-Token": token})
    assert gen_res.status_code == 200, gen_res.text
    gen_data = gen_res.json()
    assert gen_data["status"] == "success"
    assert gen_data["encounter_id"] == enc_id


def test_demo_raj_kumar_summary_preserved():
    """
    Ensure the demo patient Raj Kumar's data is intact for demo/evaluation purposes.
    """
    session_res = client.post("/api/v1/kiosk/session", json={
        "patient_id": "patient_001",
        "language": "en"
    })
    assert session_res.status_code == 200
    token = session_res.json()["session_token"]

    profile_res = client.get("/api/v1/kiosk/profile", headers={"X-Session-Token": token})
    assert profile_res.status_code == 200
    pdata = profile_res.json()
    assert pdata["demographics"]["name"] == "Raj Kumar"
    assert any("Type 2 Diabetes" in c["condition"] for c in pdata["profile_summary"]["chronic_conditions"])
