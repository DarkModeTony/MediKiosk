import os
import sys
import uuid
import time
from dotenv import load_dotenv

# Ensure we use Gemini OCR for the smoke test
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
os.environ["OCR_MODE"] = "real"
os.environ["AI_MODE"] = "real"

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models.models import KioskSession, Patient, Encounter

client = TestClient(app)

def run_smoke_test():
    image_path = r"C:\Users\Lenovo\.gemini\antigravity-ide\brain\bf50675d-7f6e-4c1c-b2ed-83599fae7760\synthetic_prescription_1789317375769.jpg"
    
    if not os.path.exists(image_path):
        print(f"FAILURE: Synthetic image not found at {image_path}")
        sys.exit(1)
        
    print("Starting Real Gemini OCR Smoke Test...")
    print(f"GEMINI_API_KEY present: {bool(os.environ.get('GEMINI_API_KEY'))}")
    
    # 1. Setup minimal database context
    db = SessionLocal()
    pat_id = str(uuid.uuid4())
    enc_id = str(uuid.uuid4())
    sess_token = "smoke_test_ocr_token"
    
    # Cleanup previous runs
    db.query(KioskSession).filter(KioskSession.session_token == sess_token).delete()
    db.commit()
    
    pat = Patient(id=pat_id, demographic_data={"name": "Smoke Test Patient"})
    enc = Encounter(id=enc_id, patient_id=pat_id, status="WAITING")
    sess = KioskSession(session_token=sess_token, data={"patient_id": pat_id, "encounter_id": enc_id})
    
    db.add(pat)
    db.add(enc)
    db.add(sess)
    db.commit()
    
    try:
        # 2. Upload Document
        print("Uploading synthetic document...")
        with open(image_path, "rb") as f:
            resp = client.post(
                "/api/v1/documents/upload",
                files={"file": ("synthetic_prescription.jpg", f, "image/jpeg")},
                data={"doc_type": "PRESCRIPTION", "session_token": sess_token}
            )
            
        if resp.status_code != 200:
            print(f"FAILURE: Upload failed: {resp.text}")
            sys.exit(1)
            
        doc_id = resp.json()["document_id"]
        print(f"SUCCESS: Document uploaded. ID: {doc_id}")
        
        # 3. Trigger OCR and Extraction Pipeline
        print("Triggering OCR + Medical Extraction Pipeline...")
        ocr_resp = client.post(f"/api/v1/documents/{doc_id}/ocr")
        
        if ocr_resp.status_code != 200:
            print(f"FAILURE: OCR Pipeline failed: {ocr_resp.text}")
            sys.exit(1)
            
        print("SUCCESS: OCR Pipeline completed.")
        
        # 4. Verify OCR Results
        print("Retrieving OCR text...")
        ocr_get = client.get(f"/api/v1/documents/{doc_id}/ocr")
        ocr_data = ocr_get.json()
        
        if not ocr_data:
            print("FAILURE: No OCR text found.")
            sys.exit(1)
            
        text_length = len(ocr_data[0].get("raw_text", ""))
        print(f"SUCCESS: OCR text length: {text_length} characters")
        print(f"--- OCR TEXT START ---\n{ocr_data[0].get('raw_text', '')}\n--- OCR TEXT END ---")
        
        # 5. Verify Extracted Entities
        print("Retrieving extracted medical entities...")
        ent_get = client.get(f"/api/v1/documents/{doc_id}/entities")
        ent_data = ent_get.json()
        
        print(f"SUCCESS: Extraction entity count: {len(ent_data)}")
        
        types_found = [e["type"] for e in ent_data]
        print(f"SUCCESS: Entity types extracted: {', '.join(set(types_found))}")
        
        print("\n--- SMOKE TEST COMPLETE ---")
        print("Persistence succeeded.")
        print(f"Document ID: {doc_id}")
        print(f"Encounter ID: {enc_id}")
        
    finally:
        # Cleanup
        db.query(KioskSession).filter(KioskSession.session_token == sess_token).delete()
        db.commit()
        db.close()

if __name__ == "__main__":
    run_smoke_test()
