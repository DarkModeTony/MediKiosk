import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import (
    Encounter, Patient, User, InvestigationOrder, InvestigationResult, AuditLog
)
from app.schemas.investigation import (
    InvestigationOrderCreate, InvestigationOrderResponse,
    AddResultsRequest, ReviewOrderRequest, InvestigationResultResponse
)
from app.api.deps import (
    get_current_user, require_doctor, verify_encounter_access, verify_patient_access
)

router = APIRouter()

def _build_order_response(order: InvestigationOrder) -> InvestigationOrderResponse:
    results_resp = [
        InvestigationResultResponse(
            id=str(r.id),
            order_id=str(r.order_id),
            parameter_name=r.parameter_name,
            value=r.value,
            unit=r.unit,
            reference_range=r.reference_range,
            abnormal_flag=r.abnormal_flag or "NORMAL",
            result_notes=r.result_notes,
            created_at=r.created_at
        )
        for r in (order.results or [])
    ]
    return InvestigationOrderResponse(
        id=str(order.id),
        encounter_id=str(order.encounter_id),
        patient_id=str(order.patient_id),
        doctor_id=str(order.doctor_id) if order.doctor_id else None,
        test_name=order.test_name,
        test_type=order.test_type,
        urgency=order.urgency,
        clinical_notes=order.clinical_notes,
        status=order.status,
        ordered_at=order.ordered_at,
        completed_at=order.completed_at,
        reviewed_at=order.reviewed_at,
        reviewed_by=str(order.reviewed_by) if order.reviewed_by else None,
        results=results_resp,
        created_at=order.created_at,
        updated_at=order.updated_at
    )

@router.post("/encounters/{encounter_id}/investigations", response_model=InvestigationOrderResponse, status_code=status.HTTP_201_CREATED)
def order_investigation(
    encounter_id: str,
    payload: InvestigationOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Place a new diagnostic investigation order for an encounter."""
    enc = verify_encounter_access(encounter_id, current_user, db)

    order = InvestigationOrder(
        encounter_id=enc.id,
        patient_id=enc.patient_id,
        doctor_id=current_user.id if current_user.role in ("DOCTOR", "PHYSICIAN", "ADMIN") else None,
        test_name=payload.test_name,
        test_type=payload.test_type.upper(),
        urgency=payload.urgency.upper(),
        clinical_notes=payload.clinical_notes,
        status="ORDERED",
        ordered_at=datetime.utcnow()
    )
    db.add(order)
    db.flush()

    audit = AuditLog(
        user_id=current_user.id if current_user else None,
        action="INVESTIGATION_ORDERED",
        target_resource=f"investigations/{order.id}",
        details={
            "test_name": order.test_name,
            "encounter_id": str(enc.id),
            "patient_id": str(enc.patient_id),
            "urgency": order.urgency
        }
    )
    db.add(audit)
    db.commit()
    db.refresh(order)
    return _build_order_response(order)

@router.get("/encounters/{encounter_id}/investigations", response_model=List[InvestigationOrderResponse])
def list_encounter_investigations(
    encounter_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all investigation orders and results for a specific encounter."""
    enc = verify_encounter_access(encounter_id, current_user, db)
    orders = db.query(InvestigationOrder).filter(
        InvestigationOrder.encounter_id == enc.id
    ).order_by(InvestigationOrder.ordered_at.desc()).all()
    return [_build_order_response(o) for o in orders]

@router.get("/patients/{patient_id}/investigations", response_model=List[InvestigationOrderResponse])
def list_patient_investigations(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all historical investigation orders and results for a patient."""
    patient = verify_patient_access(patient_id, current_user, db)
    orders = db.query(InvestigationOrder).filter(
        InvestigationOrder.patient_id == patient.id
    ).order_by(InvestigationOrder.ordered_at.desc()).all()
    return [_build_order_response(o) for o in orders]

@router.get("/investigations/{order_id}", response_model=InvestigationOrderResponse)
def get_investigation_order(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get single investigation order and its results."""
    try:
        ord_uuid = uuid.UUID(order_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Order not found")

    order = db.query(InvestigationOrder).filter(InvestigationOrder.id == ord_uuid).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    verify_encounter_access(str(order.encounter_id), current_user, db)
    return _build_order_response(order)

@router.post("/investigations/{order_id}/results", response_model=InvestigationOrderResponse)
def add_investigation_results(
    order_id: str,
    payload: AddResultsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Attach lab/diagnostic results to an investigation order.
    Automatically advances status from ORDERED/PENDING -> COMPLETED.
    """
    try:
        ord_uuid = uuid.UUID(order_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Order not found")

    order = db.query(InvestigationOrder).filter(InvestigationOrder.id == ord_uuid).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    verify_encounter_access(str(order.encounter_id), current_user, db)

    if order.status == "CANCELLED":
        raise HTTPException(status_code=400, detail="Cannot add results to a cancelled order")

    for res_in in payload.results:
        res = InvestigationResult(
            order_id=order.id,
            parameter_name=res_in.parameter_name,
            value=res_in.value,
            unit=res_in.unit,
            reference_range=res_in.reference_range,
            abnormal_flag=res_in.abnormal_flag or "NORMAL",
            result_notes=res_in.result_notes
        )
        db.add(res)

    order.status = "COMPLETED"
    order.completed_at = datetime.utcnow()
    order.updated_at = datetime.utcnow()

    audit = AuditLog(
        user_id=current_user.id if current_user else None,
        action="INVESTIGATION_RESULTS_ADDED",
        target_resource=f"investigations/{order.id}",
        details={"result_count": len(payload.results), "status": order.status}
    )
    db.add(audit)

    db.commit()
    db.refresh(order)
    return _build_order_response(order)

@router.post("/investigations/{order_id}/review", response_model=InvestigationOrderResponse)
def review_investigation_order(
    order_id: str,
    payload: ReviewOrderRequest = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_doctor)
):
    """
    Physician reviews and acknowledges diagnostic test results.
    Advances status from COMPLETED -> REVIEWED.
    """
    try:
        ord_uuid = uuid.UUID(order_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Order not found")

    order = db.query(InvestigationOrder).filter(InvestigationOrder.id == ord_uuid).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    verify_encounter_access(str(order.encounter_id), current_user, db)

    if order.status not in ("COMPLETED", "ORDERED", "PENDING"):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot review order in status '{order.status}'"
        )

    order.status = "REVIEWED"
    order.reviewed_at = datetime.utcnow()
    order.reviewed_by = current_user.id
    order.updated_at = datetime.utcnow()

    if payload and payload.notes:
        order.clinical_notes = f"{order.clinical_notes or ''}\n[Review Note]: {payload.notes}".strip()

    audit = AuditLog(
        user_id=current_user.id,
        action="INVESTIGATION_REVIEWED",
        target_resource=f"investigations/{order.id}",
        details={
            "encounter_id": str(order.encounter_id),
            "reviewed_by": str(current_user.id),
            "reviewed_at": order.reviewed_at.isoformat()
        }
    )
    db.add(audit)

    db.commit()
    db.refresh(order)
    return _build_order_response(order)

@router.post("/investigations/{order_id}/cancel", response_model=InvestigationOrderResponse)
def cancel_investigation_order(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancel an investigation order."""
    try:
        ord_uuid = uuid.UUID(order_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Order not found")

    order = db.query(InvestigationOrder).filter(InvestigationOrder.id == ord_uuid).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    verify_encounter_access(str(order.encounter_id), current_user, db)

    if order.status == "REVIEWED":
        raise HTTPException(status_code=400, detail="Cannot cancel an already reviewed order")

    order.status = "CANCELLED"
    order.updated_at = datetime.utcnow()

    audit = AuditLog(
        user_id=current_user.id if current_user else None,
        action="INVESTIGATION_CANCELLED",
        target_resource=f"investigations/{order.id}",
        details={"status": "CANCELLED"}
    )
    db.add(audit)
    db.commit()
    db.refresh(order)
    return _build_order_response(order)
