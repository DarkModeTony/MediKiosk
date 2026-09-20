import os
import json
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from app.models.models import (
    DocTalkNotification,
    DocTalkConsultation,
    AuditLog,
    User,
    Hospital,
)
from app.services.doctalk_session_manager import session_manager

logger = logging.getLogger("doctalk.notifications")

# Configurable expiry duration for pending DocTalk requests (default: 10 minutes)
DEFAULT_EXPIRY_MINUTES = int(os.getenv("DOCTALK_REQUEST_EXPIRY_MINUTES", "10"))


def get_request_expiry_minutes() -> int:
    try:
        val = int(os.getenv("DOCTALK_REQUEST_EXPIRY_MINUTES", str(DEFAULT_EXPIRY_MINUTES)))
        return max(1, val)
    except ValueError:
        return DEFAULT_EXPIRY_MINUTES


def create_doctalk_notification(
    db: Session,
    user_id: Any,
    event_type: str,
    title: str,
    message: str,
    consultation_id: Optional[Any] = None,
    encounter_id: Optional[Any] = None,
    severity: str = "INFO",
    meta_data: Optional[Dict[str, Any]] = None,
    auto_commit: bool = True,
) -> DocTalkNotification:
    """
    Creates and persists a DocTalkNotification for a physician.
    Optionally relays the notification over active room WebSockets if a session is underway.
    """
    u_uuid = uuid.UUID(str(user_id))
    c_uuid = uuid.UUID(str(consultation_id)) if consultation_id else None
    e_uuid = uuid.UUID(str(encounter_id)) if encounter_id else None

    notification = DocTalkNotification(
        user_id=u_uuid,
        consultation_id=c_uuid,
        encounter_id=e_uuid,
        event_type=event_type,
        title=title,
        message=message,
        severity=severity,
        is_read=False,
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        meta_data=meta_data or {},
    )
    db.add(notification)

    if auto_commit:
        db.commit()
        db.refresh(notification)

    logger.info(
        f"DocTalk notification created for user {u_uuid}: [{event_type}] {title}"
    )

    # Optional real-time websocket broadcast if consultation room is active
    if c_uuid:
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(
                    session_manager.broadcast_to_room(
                        consultation_id=str(c_uuid),
                        message={
                            "type": "notification",
                            "event_type": event_type,
                            "title": title,
                            "message": message,
                            "severity": severity,
                            "user_id": str(u_uuid),
                        },
                    )
                )
        except Exception as ws_err:
            logger.debug(f"Websocket notification broadcast skipped or failed: {ws_err}")

    return notification


def check_and_expire_pending_requests(db: Session) -> List[DocTalkConsultation]:
    """
    Sweeper that safely expires pending DocTalk requests exceeding validity window.
    Transitions status -> EXPIRED, logs audit trail, and notifies treating doctor.
    """
    expiry_minutes = get_request_expiry_minutes()
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    cutoff_time = now - timedelta(minutes=expiry_minutes)

    # Find pending requests past explicit expires_at OR past created_at + cutoff
    pending_query = db.query(DocTalkConsultation).filter(
        DocTalkConsultation.status == "REQUESTED",
    )

    all_pending = pending_query.all()
    expired_list: List[DocTalkConsultation] = []

    for consult in all_pending:
        is_expired = False
        if consult.expires_at:
            if consult.expires_at <= now:
                is_expired = True
        elif consult.created_at and consult.created_at <= cutoff_time:
            is_expired = True

        if is_expired:
            consult.status = "EXPIRED"
            if not consult.expires_at:
                consult.expires_at = now
            expired_list.append(consult)

            # Audit log
            audit = AuditLog(
                user_id=consult.requesting_doctor_id,
                action="DOCTALK_EXPIRED",
                target_resource=f"doctalk_consultations/{consult.id}",
                details={
                    "requester": str(consult.requesting_doctor_id),
                    "requesting_hospital": str(consult.requesting_hospital_id),
                    "specialist": str(consult.specialist_id) if consult.specialist_id else None,
                    "patient": str(consult.patient_id),
                    "encounter": str(consult.encounter_id),
                    "timestamps": now.isoformat(),
                    "actions": "DOCTALK_EXPIRED",
                    "reason": f"Request pending beyond validity period of {expiry_minutes} minutes.",
                },
            )
            db.add(audit)

            # Notify treating doctor
            create_doctalk_notification(
                db=db,
                user_id=consult.requesting_doctor_id,
                consultation_id=consult.id,
                encounter_id=consult.encounter_id,
                event_type="DOCTALK_EXPIRED",
                title="DocTalk Request Expired",
                message=f"Your consultation request for {consult.specialty} expired after {expiry_minutes} minutes without a specialist response.",
                severity="WARNING",
                meta_data={
                    "consultation_id": str(consult.id),
                    "encounter_id": str(consult.encounter_id),
                    "specialty": consult.specialty,
                    "urgency": consult.urgency,
                    "expiry_minutes": expiry_minutes,
                },
                auto_commit=False,
            )

    if expired_list:
        db.commit()
        logger.info(f"Safely expired {len(expired_list)} pending DocTalk consultation requests.")

    return expired_list
