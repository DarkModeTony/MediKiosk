import os
import time
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import httpx

from app.database import Base
from app.models.models import Document, DocumentOCR, DocumentEntity, KioskSession, Encounter, Patient

# Ensure we're hitting local server
os.environ["OCR_MODE"] = "gemini"
os.environ["EXTRACTION_MODE"] = "gemini"

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

SQLALCHEMY_DATABASE_URL = os.environ.get("DATABASE_URL")
if not SQLALCHEMY_DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is not set.")

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def verify_gemini_api_key():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not found in environment.")
        return False
    print(f"GEMINI_API_KEY present: True")
    return True

def run_smoke_test():
    print("Starting Real Gemini Medical Extraction Smoke Test...")
    
    if not verify_gemini_api_key():
        return
        
    db = SessionLocal()
    
    # 1. Setup Data
    test_pat_uuid = "12345678-0000-0000-0000-000000000001"
    test_enc_uuid = "12345678-0000-0000-0000-000000000002"
    
    # Cleanup previous run
    docs = db.query(Document).filter(Document.encounter_id == test_enc_uuid).all()
    for d in docs:
        db.query(DocumentEntity).filter(DocumentEntity.document_id == d.id).delete()
        db.query(DocumentOCR).filter(DocumentOCR.document_id == d.id).delete()
    db.query(Document).filter(Document.encounter_id == test_enc_uuid).delete()
    db.query(KioskSession).filter(KioskSession.session_token == "smoke_test_token").delete()
    db.query(Encounter).filter(Encounter.id == test_enc_uuid).delete()
    db.query(Patient).filter(Patient.id == test_pat_uuid).delete()
    db.commit()
    
    pat = Patient(id=test_pat_uuid, demographic_data={"name": "Raj Kumar", "age": 68})
    db.add(pat)
    
    enc = Encounter(id=test_enc_uuid, patient_id=test_pat_uuid, status="WAITING")
    db.add(enc)
    
    sess = KioskSession(session_token="smoke_test_token", data={"patient_id": test_pat_uuid, "encounter_id": test_enc_uuid})
    db.add(sess)
    db.commit()
    
    # 2. Upload Synthetic Image
    print("Uploading synthetic document...")
    
    img_path = "C:/Users/Lenovo/.gemini/antigravity-ide/brain/bf50675d-7f6e-4c1c-b2ed-83599fae7760/synthetic_prescription_1789317375769.jpg"
    with open(img_path, "rb") as f:
        img_byte_arr = f.read()
    
    # Actually call the local endpoints directly to bypass FastAPI test client network issues
    # Or just use the test client!
    from fastapi.testclient import TestClient
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
    
    resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("mock_medical_doc.jpg", img_byte_arr, "image/jpeg")},
        data={"doc_type": "CLINICAL_NOTE", "session_token": "smoke_test_token"}
    )
    
    if resp.status_code != 200:
        print(f"FAILED: Upload error: {resp.json()}")
        return
        
    doc_id = resp.json()["document_id"]
    print(f"SUCCESS: Document uploaded. ID: {doc_id}")
    
    # 3. Trigger OCR + Extraction Pipeline
    print("Triggering OCR + Medical Extraction Pipeline...")
    
    # Force the api endpoints to load the real providers for this test
    # (Because app.api.endpoints.documents caches the instances)
    from ai.ocr.gemini_provider import GeminiOCRProvider
    from ai.medical_extraction.gemini_provider import GeminiExtractionProvider
    from unittest.mock import patch
    
    with patch("app.api.endpoints.documents.ocr_provider", GeminiOCRProvider()), \
         patch("app.api.endpoints.documents.extraction_provider", GeminiExtractionProvider()):
         
         ocr_resp = client.post(f"/api/v1/documents/{doc_id}/ocr")
         
    if ocr_resp.status_code != 200:
        print(f"FAILED: Pipeline error: {ocr_resp.json()}")
        return
        
    print("SUCCESS: Pipeline completed.")
    
    # 4. Verification
    print("Retrieving extracted medical entities...")
    ent_resp = client.get(f"/api/v1/documents/{doc_id}/entities")
    if ent_resp.status_code != 200:
        print(f"FAILED: Entity retrieval error: {ent_resp.json()}")
        return
        
    entities = ent_resp.json()
    print(f"SUCCESS: Extraction entity count: {len(entities)}")
    
    has_med = False
    
    for e in entities:
        t = e.get('type', 'UNKNOWN')
        val = str(e.get('value', e))
        print(f" - [{t}] {val}")
        if t == 'MEDICATION' and 'Aspirin' in val and '75' in val:
            has_med = True
            
    # Saftey checks
    if len(entities) == 0:
        print("FAILED: Extraction returned zero entities.")
        return
        
    if not has_med: print("FAILED: Missing medication (Aspirin 75 mg)")
        
    if has_med:
        print("\n--- SMOKE TEST COMPLETE ---")
        print("Persistence succeeded.")
        print("Retrieval: SUCCESS")
    else:
        print("\nFAILED: Not all expected entities were extracted and persisted successfully.")
    
if __name__ == "__main__":
    run_smoke_test()
