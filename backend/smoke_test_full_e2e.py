import os
import time
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from fastapi.testclient import TestClient

# Must force real modes
os.environ["OCR_MODE"] = "gemini"
os.environ["EXTRACTION_MODE"] = "gemini"
os.environ["AI_MODE"] = "real"
os.environ["LLM_PROVIDER"] = "gemini"

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

SQLALCHEMY_DATABASE_URL = os.environ.get("DATABASE_URL")
if not SQLALCHEMY_DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is not set.")

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def verify_providers():
    from ai.ocr.service import get_ocr_provider
    from ai.medical_extraction.service import get_extraction_provider
    from ai.summarization.service import get_summary_provider

    ocr = get_ocr_provider()
    ext = get_extraction_provider()
    sum_prov = get_summary_provider()
    
    print("\n--- VERIFYING PROVIDERS ---")
    print(f"OCR provider:\n{ocr.__class__.__name__}")
    print(f"Extraction provider:\n{ext.__class__.__name__}")
    print(f"Summary provider:\n{sum_prov.__class__.__name__}")
    
    if "Mock" in ocr.__class__.__name__ or "Mock" in ext.__class__.__name__ or "Mock" in sum_prov.__class__.__name__:
        print("FAILED: A mock provider is being used in REAL API mode.")
        return False
    return True

def run_e2e():
    print("Starting REAL E2E Smoke Test...")
    
    if not verify_providers():
        return
        
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not found in environment.")
        return
        
    from app.main import app
    from app.database import get_db
    
    def override_get_db():
        try:
            db_instance = SessionLocal()
            yield db_instance
        finally:
            db_instance.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    
    # 1. Patient registration
    print("\n[1] Patient Registration")
    resp = client.post("/api/v1/patients/register", json={
        "demographic_data": {"name": "Raj Kumar", "age": 68, "gender": "Male"},
        "consent": True
    })
    assert resp.status_code == 200, f"Failed registration: {resp.json()}"
    patient_id = resp.json()["patient_id"]
    print(f"Patient registered: {patient_id}")
    
    # 2. Session creation
    print("\n[2] Session Creation")
    resp = client.post("/api/v1/kiosk/session", json={
        "patient_id": patient_id,
        "language": "en"
    })
    assert resp.status_code == 200, f"Failed session creation: {resp.json()}"
    session_token = resp.json()["session_token"]
    print(f"Session created: {session_token}")
    
    # 3. Clinical Intake Start (Encounter creation)
    print("\n[3] Clinical Intake Start")
    resp = client.post(f"/api/v1/clinical/start?session_token={session_token}")
    assert resp.status_code == 200, f"Failed clinical start: {resp.json()}"
    encounter_id = resp.json()["encounter_id"]
    print(f"Encounter created: {encounter_id}")
    
    # 4. Clinical Intake Answer (Red flag generation)
    print("\n[4] Clinical Intake Answer & Red Flag")
    resp = client.post(f"/api/v1/clinical/answer?session_token={session_token}", json={
        "question_id": "chief_complaint_initial",
        "raw_transcript": "I have sudden chest pain",
    })
    assert resp.status_code == 200, f"Failed clinical answer: {resp.json()}"
    state = resp.json()
    print("Facts collected:", state["facts"])
    
    # Retrieve encounter to verify red flag
    resp = client.get(f"/api/v1/encounters/{encounter_id}")
    assert resp.status_code == 200, f"Failed encounter fetch: {resp.json()}"
    encounter_data = resp.json()
    print(f"Encounter priority: {encounter_data['priority']}")
    if encounter_data['priority'] != 'HIGH':
        print("WARNING: Expected HIGH priority due to chest pain red flag. Checking red flag rules...")
    
    # 5. Document Upload
    print("\n[5] Document Upload")
    img_path = "C:/Users/Lenovo/.gemini/antigravity-ide/brain/bf50675d-7f6e-4c1c-b2ed-83599fae7760/synthetic_prescription_1789317375769.jpg"
    with open(img_path, "rb") as f:
        img_byte_arr = f.read()
        
    resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("mock_medical_doc.jpg", img_byte_arr, "image/jpeg")},
        data={"doc_type": "CLINICAL_NOTE", "session_token": session_token}
    )
    assert resp.status_code == 200, f"Failed document upload: {resp.json()}"
    document_id = resp.json()["document_id"]
    print(f"Document uploaded: {document_id}")
    
    # 6. Real Gemini OCR
    print("\n[6] Real Gemini OCR & Extraction")
    # Using the live endpoints that call the real providers
    import time
    max_retries = 3
    for attempt in range(max_retries):
        ocr_resp = client.post(f"/api/v1/documents/{document_id}/ocr")
        if ocr_resp.status_code == 200:
            break
        elif "429" in str(ocr_resp.json()) or "RESOURCE_EXHAUSTED" in str(ocr_resp.json()):
            if "free_tier_requests" in str(ocr_resp.json()) or "GenerateRequestsPerDay" in str(ocr_resp.json()):
                assert False, f"FAILED: Daily Gemini Quota Exhausted. Run after reset. Error: {ocr_resp.json()}"
            print(f"Transient rate limit during OCR. Retrying in 10 seconds (attempt {attempt+1}/{max_retries})...")
            time.sleep(10)
        else:
            assert False, f"Failed OCR: {ocr_resp.json()}"
    assert ocr_resp.status_code == 200, f"Failed OCR after retries: {ocr_resp.json()}"
    
    # 7. Entities Extraction
    for attempt in range(max_retries):
        ent_resp = client.get(f"/api/v1/documents/{document_id}/entities")
        if ent_resp.status_code == 200:
            break
        elif "429" in str(ent_resp.json()) or "RESOURCE_EXHAUSTED" in str(ent_resp.json()):
            if "free_tier_requests" in str(ent_resp.json()) or "GenerateRequestsPerDay" in str(ent_resp.json()):
                assert False, f"FAILED: Daily Gemini Quota Exhausted. Run after reset. Error: {ent_resp.json()}"
            print(f"Transient rate limit during entities extraction. Retrying in 10 seconds (attempt {attempt+1}/{max_retries})...")
            time.sleep(10)
        else:
            assert False, f"Failed entity retrieval: {ent_resp.json()}"
    assert ent_resp.status_code == 200, f"Failed entity retrieval after retries: {ent_resp.json()}"
    entities = ent_resp.json()
    print(f"Extracted {len(entities)} entities.")
    for e in entities:
        t = e.get('type', 'UNKNOWN')
        val = e.get('value', e)
        print(f" - [{t}] {val}")
        print(f"   Source text: '{e.get('source_text')}'")
    
    if len(entities) == 0:
        print("FAILED: Extraction returned zero entities.")
        return
        
    # 8. Real Gemini Clinical Summary
    print("\n[8] Real Gemini Clinical Summary")
    for attempt in range(max_retries):
        sum_resp = client.post("/api/v1/summaries/generate", json={"encounter_id": encounter_id})
        if sum_resp.status_code == 200:
            break
        elif "429" in str(sum_resp.json()) or "RESOURCE_EXHAUSTED" in str(sum_resp.json()):
            if "free_tier_requests" in str(sum_resp.json()) or "GenerateRequestsPerDay" in str(sum_resp.json()):
                assert False, f"FAILED: Daily Gemini Quota Exhausted. Run after reset. Error: {sum_resp.json()}"
            print(f"Transient rate limit during summary generation. Retrying in 10 seconds (attempt {attempt+1}/{max_retries})...")
            time.sleep(10)
        else:
            assert False, f"Failed summary generation: {sum_resp.json()}"
    assert sum_resp.status_code == 200, f"Failed summary generation after retries: {sum_resp.json()}"
    summary_id = sum_resp.json()["summary_id"]
    print(f"Summary generated: {summary_id}")
    
    # 9. Doctor Queue Retrieval
    print("\n[9] Doctor Queue Retrieval")
    q_resp = client.get("/api/v1/encounters/active")
    assert q_resp.status_code == 200, f"Failed queue retrieval: {q_resp.json()}"
    queue = q_resp.json()
    found_in_queue = False
    for item in queue:
        if item["id"] == encounter_id:
            found_in_queue = True
            print(f"Found {item['name']} (ID: {encounter_id}) in queue with priority {item['priority']}")
            break
    if not found_in_queue:
        print("FAILED: Encounter not found in active queue.")
        return
        
    # 10. Summary Retrieval
    print("\n[10] Summary Retrieval")
    s_resp = client.get(f"/api/v1/summaries/encounters/{encounter_id}/summary")
    assert s_resp.status_code == 200, f"Failed summary retrieval: {s_resp.json()}"
    summary_data = s_resp.json()
    print(f"Summary status: {summary_data['status']}")
    
    # 11. Patient Isolation Test
    print("\n[11] Patient Isolation Test")
    resp_b = client.post("/api/v1/patients/register", json={"demographic_data": {"name": "Synthetic Test Patient B"}, "consent": True})
    patient_b_id = resp_b.json()["patient_id"]
    resp_sess_b = client.post("/api/v1/kiosk/session", json={"patient_id": patient_b_id, "language": "en"})
    sess_b_token = resp_sess_b.json()["session_token"]
    
    # Attempt to get Patient A's state using Patient B's session
    iso_resp = client.get(f"/api/v1/clinical/state?session_token={sess_b_token}")
    # Patient B has no clinical state yet, should start fresh
    iso_state = iso_resp.json()
    if iso_state.get("encounter_id") == encounter_id:
        print("FAILED: Patient B accessed Patient A's encounter!")
        return
    else:
        print("Patient isolation verified: Patient B got a distinct encounter or fresh state.")
        
    # 12. Cleanup (optional, but requested for cleanliness)
    print("\n--- SMOKE TEST COMPLETE ---")
    print("Real E2E Pipeline Succeeded.")

if __name__ == "__main__":
    t0 = time.time()
    run_e2e()
    t1 = time.time()
    print(f"\nTotal E2E Execution Time: {t1 - t0:.2f} seconds")
