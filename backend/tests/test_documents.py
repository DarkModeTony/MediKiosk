import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from io import BytesIO

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
os.environ["OCR_MODE"] = "mock"  # Force mock for unit tests
os.environ["AI_MODE"] = "mock"
os.environ["EXTRACTION_MODE"] = "mock"

from app.main import app
from app.database import Base, get_db
from app.models.models import KioskSession, Encounter, Patient, Document, DocumentOCR, DocumentEntity

SQLALCHEMY_DATABASE_URL = os.environ.get("DATABASE_URL")

engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture
def setup_data():
    db = TestingSessionLocal()
    test_pat_uuid = "00000000-0000-0000-0000-000000000001"
    test_enc_uuid = "00000000-0000-0000-0000-000000000002"
    
    # Pre-cleanup in case previous run failed
    db.query(KioskSession).filter(KioskSession.session_token == "test_token").delete()
    
    docs = db.query(Document).filter(Document.encounter_id == test_enc_uuid).all()
    for d in docs:
        db.query(DocumentEntity).filter(DocumentEntity.document_id == d.id).delete()
        db.query(DocumentOCR).filter(DocumentOCR.document_id == d.id).delete()
    db.query(Document).filter(Document.encounter_id == test_enc_uuid).delete()
    
    db.query(Encounter).filter(Encounter.id == test_enc_uuid).delete()
    db.query(Patient).filter(Patient.id == test_pat_uuid).delete()
    db.commit()
    
    pat = Patient(id=test_pat_uuid, demographic_data={"name": "test"})
    db.add(pat)
    
    enc = Encounter(id=test_enc_uuid, patient_id=test_pat_uuid, status="WAITING")
    db.add(enc)
    
    sess = KioskSession(session_token="test_token", data={"patient_id": test_pat_uuid, "encounter_id": test_enc_uuid})
    db.add(sess)
    db.commit()
    
    try:
        yield
    finally:
        # Cleanup
        db.query(KioskSession).filter(KioskSession.session_token == "test_token").delete()
        
        docs = db.query(Document).filter(Document.encounter_id == test_enc_uuid).all()
        for d in docs:
            db.query(DocumentEntity).filter(DocumentEntity.document_id == d.id).delete()
            db.query(DocumentOCR).filter(DocumentOCR.document_id == d.id).delete()
        db.query(Document).filter(Document.encounter_id == test_enc_uuid).delete()
        
        db.query(Encounter).filter(Encounter.id == test_enc_uuid).delete()
        db.query(Patient).filter(Patient.id == test_pat_uuid).delete()
        db.commit()

def test_upload_document(setup_data):
    file_content = b"fake image data"
    file = BytesIO(file_content)
    file.name = "test.jpg"
    
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.jpg", file, "image/jpeg")},
        data={"doc_type": "PRESCRIPTION", "session_token": "test_token"}
    )
    
    assert response.status_code == 200
    assert "document_id" in response.json()
    assert response.json()["status"] == "UPLOADED"

def test_upload_invalid_type(setup_data):
    file = BytesIO(b"fake text")
    
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.txt", file, "text/plain")},
        data={"doc_type": "PRESCRIPTION", "session_token": "test_token"}
    )
    
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]

def test_ocr_and_extraction(setup_data):
    # Upload first
    file = BytesIO(b"amlodipine 5 mg once daily")
    resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("mock_prescription.jpg", file, "image/jpeg")},
        data={"doc_type": "PRESCRIPTION", "session_token": "test_token"}
    )
    doc_id = resp.json()["document_id"]
    
    # Trigger OCR
    from unittest.mock import patch
    from ai.ocr.mock_provider import MockOCRProvider
    from ai.medical_extraction.mock_provider import MockExtractionProvider
    
    with patch("app.api.endpoints.documents.ocr_provider", MockOCRProvider()), \
         patch("app.api.endpoints.documents.extraction_provider", MockExtractionProvider()):
        ocr_resp = client.post(f"/api/v1/documents/{doc_id}/ocr")
        if ocr_resp.status_code != 200:
            print("OCR ERROR:", ocr_resp.json())
        assert ocr_resp.status_code == 200
    
    # Get Entities
    ent_resp = client.get(f"/api/v1/documents/{doc_id}/entities")
    assert ent_resp.status_code == 200
    entities = ent_resp.json()
    assert len(entities) > 0
    
    # Check that verification state is AI_EXTRACTED
    assert entities[0]["status"] == "AI_EXTRACTED"
    
    # Confirm endpoint
    confirm_payload = {
        "entities": [
            {
                "entity_id": entities[0]["id"],
                "corrected_value": {"name": "Corrected Med"},
                "status": "PATIENT_CORRECTED"
            }
        ]
    }
    conf_resp = client.post(f"/api/v1/documents/{doc_id}/confirm", json=confirm_payload)
    assert conf_resp.status_code == 200
    
    # Verify status changed
    ent_resp2 = client.get(f"/api/v1/documents/{doc_id}/entities")
    updated_ent = next(e for e in ent_resp2.json() if e["id"] == entities[0]["id"])
    assert updated_ent["status"] == "PATIENT_CORRECTED"
