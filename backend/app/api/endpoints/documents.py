import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

from app.database import get_db
from app.models.models import (
    Document,
    DocumentOCR,
    DocumentEntity,
    KioskSession,
    Encounter,
    User,
    Hospital,
    DocTalkConsultation,
    DocTalkConsultationNote,
)
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
    encounter_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    patient = verify_patient_access(patient_id, current_user, db)
    
    # Gathers documents and consultations connected to patient_id directly or via encounters
    enc_query = db.query(Encounter).filter(Encounter.patient_id == patient.id)
    if encounter_id:
        try:
            import uuid as _uuid
            enc_uuid = _uuid.UUID(encounter_id)
            enc_query = enc_query.filter(Encounter.id == enc_uuid)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid encounter_id format")

    encounters = enc_query.all()
    enc_ids = [e.id for e in encounters]
    
    events = []

    # 1. Documents
    if enc_ids:
        docs = db.query(Document).filter(Document.encounter_id.in_(enc_ids)).all()
        for doc in docs:
            entities = db.query(DocumentEntity).filter(DocumentEntity.document_id == doc.id).all()
            ent_list = [{"type": e.entity_type, "value": e.value, "status": e.status} for e in entities]
            
            events.append({
                "date": doc.document_date.isoformat() if doc.document_date else None,
                "date_known": doc.document_date is not None,
                "type": "DOCUMENT",
                "document_id": str(doc.id),
                "document_type": doc.doc_type,
                "entities": ent_list,
                "encounter_id": str(doc.encounter_id) if doc.encounter_id else None,
            })

    # 2. DocTalk consultations and opinions
    if enc_ids:
        consultations = db.query(DocTalkConsultation).filter(
            DocTalkConsultation.encounter_id.in_(enc_ids)
        ).all()

        for consult in consultations:
            # Resolve specialist & hospital attribution
            spec = db.query(User).filter(User.id == consult.specialist_id).first() if consult.specialist_id else None
            spec_name = spec.display_name or (f"Dr. {spec.username.capitalize()}" if spec else None)
            spec_hosp = db.query(Hospital).filter(Hospital.id == consult.specialist_hospital_id).first() if consult.specialist_hospital_id else None
            spec_hosp_name = spec_hosp.name if spec_hosp else None

            # Milestone 1: 🩺 DocTalk requested
            if consult.created_at:
                events.append({
                    "date": consult.created_at.isoformat(),
                    "date_known": True,
                    "type": "DOCTALK_REQUESTED",
                    "title": "🩺 DocTalk requested",
                    "consultation_id": str(consult.id),
                    "encounter_id": str(consult.encounter_id),
                    "specialty": consult.specialty,
                    "reason": consult.reason,
                    "urgency": consult.urgency,
                    "requested_duration_minutes": consult.requested_duration_minutes,
                    "specialist_name": spec_name or "Any Available Specialist",
                    "specialist_hospital": spec_hosp_name,
                })

            # Milestone 2: ✓ Specialist accepted
            if consult.accepted_at:
                events.append({
                    "date": consult.accepted_at.isoformat(),
                    "date_known": True,
                    "type": "DOCTALK_ACCEPTED",
                    "title": "✓ Specialist accepted",
                    "consultation_id": str(consult.id),
                    "encounter_id": str(consult.encounter_id),
                    "specialty": consult.specialty,
                    "specialist_name": spec_name,
                    "specialist_hospital": spec_hosp_name,
                })

            # Milestone 3: 🟢 Consultation started
            if consult.started_at:
                events.append({
                    "date": consult.started_at.isoformat(),
                    "date_known": True,
                    "type": "DOCTALK_STARTED",
                    "title": "🟢 Consultation started",
                    "consultation_id": str(consult.id),
                    "encounter_id": str(consult.encounter_id),
                    "specialty": consult.specialty,
                    "specialist_name": spec_name,
                    "specialist_hospital": spec_hosp_name,
                    "duration_minutes": consult.requested_duration_minutes,
                })

            # Milestone 4: ✓ Consultation completed
            if consult.completed_at:
                events.append({
                    "date": consult.completed_at.isoformat(),
                    "date_known": True,
                    "type": "DOCTALK_COMPLETED",
                    "title": "✓ Consultation completed",
                    "consultation_id": str(consult.id),
                    "encounter_id": str(consult.encounter_id),
                    "specialty": consult.specialty,
                    "specialist_name": spec_name,
                    "specialist_hospital": spec_hosp_name,
                })

            # Milestone 5: 📄 Specialist opinion added
            notes = db.query(DocTalkConsultationNote).filter(
                DocTalkConsultationNote.consultation_id == consult.id
            ).order_by(DocTalkConsultationNote.created_at.asc()).all()

            for note in notes:
                note_spec = db.query(User).filter(User.id == note.specialist_id).first() if note.specialist_id else spec
                note_spec_name = note_spec.display_name or (f"Dr. {note_spec.username.capitalize()}" if note_spec else spec_name)
                note_hosp = db.query(Hospital).filter(Hospital.id == note.specialist_hospital_id).first() if note.specialist_hospital_id else spec_hosp
                note_hosp_name = note_hosp.name if note_hosp else spec_hosp_name

                events.append({
                    "date": note.created_at.isoformat() if note.created_at else None,
                    "date_known": note.created_at is not None,
                    "type": "DOCTALK_OPINION",
                    "title": "📄 Specialist opinion added",
                    "consultation_id": str(consult.id),
                    "note_id": str(note.id),
                    "encounter_id": str(consult.encounter_id),
                    "specialty": consult.specialty,
                    "specialist_name": note_spec_name,
                    "specialist_hospital": note_hosp_name,
                    "clinical_opinion": note.clinical_opinion,
                    "recommendations": note.recommendations,
                    "further_evaluation": note.further_evaluation,
                    "follow_up": note.follow_up,
                })
        
    # Sort chronologically by date
    events.sort(key=lambda x: x.get("date") or "")
    
    return {
        "patient_id": str(patient.id),
        "events": events
    }
