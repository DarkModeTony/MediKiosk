import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

from app.database import get_db
from app.models.models import Document, DocumentOCR, DocumentEntity, KioskSession, Encounter, User
from app.services.storage import get_document_storage
from app.api.deps import get_current_user, verify_document_access, verify_patient_access
from ai.ocr.service import get_ocr_provider
from ai.medical_extraction.service import get_extraction_provider
from ai.medical_extraction.models import EntityType, VerificationStatus

router = APIRouter()
storage = get_document_storage()
ocr_provider = get_ocr_provider()
extraction_provider = get_extraction_provider()

ALLOWED_MIME_TYPES = ["image/jpeg", "image/png", "application/pdf"]
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    doc_type: str = Form("OTHER"),
    session_token: str = Form(...),
    db: Session = Depends(get_db)
):
    # Security / Auth via session
    kiosk_session = db.query(KioskSession).filter(KioskSession.session_token == session_token).first()
    if not kiosk_session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    patient_id = kiosk_session.data.get("patient_id")
    encounter_id = kiosk_session.data.get("encounter_id")
    
    if not patient_id:
        raise HTTPException(status_code=400, detail="No patient associated with session")
        
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported file type")
        
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large")
        
    # Reset stream for storage
    await file.seek(0)
    storage_id = storage.save_document(file.file, file.filename, patient_id)
    
    doc = Document(
        encounter_id=encounter_id,
        file_path=storage_id,
        doc_type=doc_type,
        status="UPLOADED"
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    
    return {"document_id": str(doc.id), "status": doc.status}

@router.post("/{document_id}/ocr")
def process_ocr(document_id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    doc.status = "PROCESSING"
    db.commit()
    
    try:
        # OCR Pipeline
        filepath = storage.get_document_path(doc.file_path)
        ocr_results = ocr_provider.process(filepath)
        
        for result in ocr_results:
            doc_ocr = DocumentOCR(
                document_id=doc.id,
                raw_text=result.raw_text,
                engine_used="PaddleOCR" if "paddle" in os.environ.get("AI_MODE", "mock").lower() else "MockOCR",
                page_number=result.page_number,
                confidence=result.confidence,
                bounding_boxes=result.bounding_boxes
            )
            db.add(doc_ocr)
            
            # Medical Entity Extraction Pipeline
            extracted = extraction_provider.extract(result.raw_text, result.page_number)
            
            if extracted.document_date:
                from dateutil.parser import parse
                try:
                    doc.document_date = parse(extracted.document_date)
                except:
                    pass
            
            # Save medications
            for med in extracted.medications:
                db.add(DocumentEntity(
                    document_id=doc.id,
                    entity_type=EntityType.MEDICATION.value,
                    value=med.model_dump(),
                    confidence=1.0 if med.confidence_level == "HIGH" else 0.5,
                    source_text=med.source_text,
                    page_number=med.page_number
                ))
            # Save labs
            for lab in extracted.lab_results:
                db.add(DocumentEntity(
                    document_id=doc.id,
                    entity_type=EntityType.LAB_RESULT.value,
                    value=lab.model_dump(),
                    confidence=1.0 if lab.confidence_level == "HIGH" else 0.5,
                    source_text=lab.source_text,
                    page_number=lab.page_number
                ))
            # Save diagnoses
            for diag in extracted.diagnoses:
                db.add(DocumentEntity(
                    document_id=doc.id,
                    entity_type=EntityType.DIAGNOSIS.value,
                    value=diag.model_dump(),
                    confidence=1.0 if diag.confidence_level == "HIGH" else 0.5,
                    source_text=diag.source_text,
                    page_number=diag.page_number
                ))
            # Save patient info
            for p in extracted.patient_info:
                db.add(DocumentEntity(
                    document_id=doc.id,
                    entity_type=EntityType.PATIENT_INFO.value,
                    value=p.model_dump(),
                    confidence=1.0 if p.confidence_level == "HIGH" else 0.5,
                    source_text=p.source_text,
                    page_number=p.page_number
                ))
            # Save other
            for o in extracted.other:
                db.add(DocumentEntity(
                    document_id=doc.id,
                    entity_type=EntityType.OTHER.value,
                    value=o.model_dump(),
                    confidence=1.0 if o.confidence_level == "HIGH" else 0.5,
                    source_text=o.source_text,
                    page_number=o.page_number
                ))
                
        doc.status = "COMPLETED"
        db.commit()
        return {"status": "success"}
    except Exception as e:
        doc.status = "FAILED"
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{document_id}")
def get_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    doc = verify_document_access(document_id, current_user, db)
    return {
        "id": str(doc.id),
        "doc_type": doc.doc_type,
        "status": doc.status,
        "document_date": doc.document_date
    }

@router.get("/{document_id}/ocr")
def get_document_ocr(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    doc = verify_document_access(document_id, current_user, db)
    ocr_pages = db.query(DocumentOCR).filter(DocumentOCR.document_id == doc.id).order_by(DocumentOCR.page_number).all()
    return [{"page": o.page_number, "raw_text": o.raw_text, "confidence": o.confidence} for o in ocr_pages]

@router.get("/{document_id}/entities")
def get_document_entities(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    doc = verify_document_access(document_id, current_user, db)
    entities = db.query(DocumentEntity).filter(DocumentEntity.document_id == doc.id).all()
    
    # Group them up for the frontend
    return [
        {
            "id": str(e.id),
            "type": e.entity_type,
            "value": e.value,
            "confidence": e.confidence,
            "status": e.status,
            "source_text": e.source_text
        }
        for e in entities
    ]

class ConfirmEntityRequest(BaseModel):
    entity_id: str
    corrected_value: dict
    status: str = "PATIENT_CORRECTED"

class ConfirmDocumentRequest(BaseModel):
    entities: List[ConfirmEntityRequest]

@router.post("/{document_id}/confirm")
def confirm_document(
    document_id: str,
    payload: ConfirmDocumentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    doc = verify_document_access(document_id, current_user, db)
    for ent_payload in payload.entities:
        db_ent = db.query(DocumentEntity).filter(
            DocumentEntity.id == ent_payload.entity_id, 
            DocumentEntity.document_id == doc.id
        ).first()
        if db_ent:
            # We don't overwrite the original source_text or original raw text. 
            # We just update the structured value and status.
            db_ent.value = ent_payload.corrected_value
            db_ent.status = ent_payload.status
        else:
            raise HTTPException(status_code=404, detail=f"Entity {ent_payload.entity_id} not found")
    db.commit()
    return {"status": "success"}

@router.get("/patients/{patient_id}/timeline")
def get_patient_timeline(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    patient = verify_patient_access(patient_id, current_user, db)
    # This gathers documents connected to patient_id directly or via encounters
    encounters = db.query(Encounter).filter(Encounter.patient_id == patient.id).all()
    enc_ids = [e.id for e in encounters]
    
    docs = db.query(Document).filter(Document.encounter_id.in_(enc_ids)).all()
    
    events = []
    for doc in docs:
        entities = db.query(DocumentEntity).filter(DocumentEntity.document_id == doc.id).all()
        ent_list = [{"type": e.entity_type, "value": e.value, "status": e.status} for e in entities]
        
        events.append({
            "date": doc.document_date.isoformat() if doc.document_date else None,
            "date_known": doc.document_date is not None,
            "type": "DOCUMENT",
            "document_id": str(doc.id),
            "document_type": doc.doc_type,
            "entities": ent_list
        })
        
    # Sort by date, falling back to oldest/newest or arbitrary for unknown dates
    events.sort(key=lambda x: x["date"] or "")
    
    return {
        "patient_id": str(patient.id),
        "events": events
    }
