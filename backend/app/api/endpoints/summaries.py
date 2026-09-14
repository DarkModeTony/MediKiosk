from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from pydantic import BaseModel
import datetime

from app.database import get_db
from app.models.models import Encounter, ClinicalSummary, SummaryVerification
from ai.summarization.aggregator import ClinicalDataAggregator
from ai.summarization.service import get_summary_provider
from ai.summarization.models import SummaryStatus

router = APIRouter()
provider = get_summary_provider()

class GenerateSummaryRequest(BaseModel):
    encounter_id: str

@router.post("/generate")
def generate_summary(req: GenerateSummaryRequest, db: Session = Depends(get_db)):
    encounter = db.query(Encounter).filter(Encounter.id == req.encounter_id).first()
    if not encounter:
        raise HTTPException(status_code=404, detail="Encounter not found")
        
    aggregator = ClinicalDataAggregator(db)
    input_data, source_refs = aggregator.gather_data(req.encounter_id)
    
    draft = provider.generate(input_data)
    draft.encounter_id = req.encounter_id
    
    # Attach source refs collected by the aggregator
    draft.source_references = source_refs
    
    # Check if a summary already exists
    existing = db.query(ClinicalSummary).filter(ClinicalSummary.encounter_id == req.encounter_id).first()
    if existing:
        summary_id = existing.id
        # We can either overwrite the AI DRAFT or create a new one. The requirements say:
        # "Reuse: clinical_summaries, summary_verifications if already present."
        existing.draft_content = draft.model_dump(mode="json")
        db.commit()
    else:
        new_summary = ClinicalSummary(
            encounter_id=req.encounter_id,
            draft_content=draft.model_dump(mode="json"),
            model_info={"provider": draft.provider, "version": draft.version}
        )
        db.add(new_summary)
        db.commit()
        db.refresh(new_summary)
        summary_id = new_summary.id
        
        # Add the first version to summary_verifications
        v1 = SummaryVerification(
            summary_id=summary_id,
            final_content=draft.model_dump(mode="json"),
            status=SummaryStatus.AI_DRAFT.value
        )
        db.add(v1)
        db.commit()
    
    return {"status": "success", "summary_id": str(summary_id)}

@router.get("/encounters/{encounter_id}/summary")
def get_encounter_summary(encounter_id: str, db: Session = Depends(get_db)):
    summary = db.query(ClinicalSummary).filter(ClinicalSummary.encounter_id == encounter_id).first()
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")
        
    # Get the latest verification version
    latest_v = db.query(SummaryVerification).filter(SummaryVerification.summary_id == summary.id).order_by(SummaryVerification.verified_at.desc()).first()
    
    return {
        "summary_id": str(summary.id),
        "latest_version": latest_v.final_content if latest_v else summary.draft_content,
        "status": latest_v.status if latest_v else SummaryStatus.AI_DRAFT.value,
        "original_draft": summary.draft_content
    }

class EditSummaryRequest(BaseModel):
    content: dict

@router.post("/{summary_id}/edit")
def edit_summary(summary_id: str, req: EditSummaryRequest, db: Session = Depends(get_db)):
    summary = db.query(ClinicalSummary).filter(ClinicalSummary.id == summary_id).first()
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")
        
    new_v = SummaryVerification(
        summary_id=summary_id,
        final_content=req.content,
        status=SummaryStatus.DOCTOR_EDITED.value
    )
    db.add(new_v)
    db.commit()
    return {"status": "success"}

@router.post("/{summary_id}/verify")
def verify_summary(summary_id: str, db: Session = Depends(get_db)):
    latest_v = db.query(SummaryVerification).filter(SummaryVerification.summary_id == summary_id).order_by(SummaryVerification.verified_at.desc()).first()
    if not latest_v:
        raise HTTPException(status_code=404, detail="No draft found to verify")
        
    verified = SummaryVerification(
        summary_id=summary_id,
        final_content=latest_v.final_content,
        status=SummaryStatus.DOCTOR_VERIFIED.value
    )
    db.add(verified)
    db.commit()
    return {"status": "success"}

@router.post("/{summary_id}/reject")
def reject_summary(summary_id: str, db: Session = Depends(get_db)):
    latest_v = db.query(SummaryVerification).filter(SummaryVerification.summary_id == summary_id).order_by(SummaryVerification.verified_at.desc()).first()
    if not latest_v:
        raise HTTPException(status_code=404, detail="No draft found")
        
    rejected = SummaryVerification(
        summary_id=summary_id,
        final_content=latest_v.final_content,
        status=SummaryStatus.REJECTED.value
    )
    db.add(rejected)
    db.commit()
    return {"status": "success"}
