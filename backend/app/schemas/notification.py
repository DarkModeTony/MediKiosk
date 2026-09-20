from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    consultation_id: Optional[str] = None
    encounter_id: Optional[str] = None
    event_type: str
    title: str
    message: str
    severity: str = "INFO"
    is_read: bool = False
    created_at: datetime
    meta_data: Optional[Dict[str, Any]] = None


class NotificationCountResponse(BaseModel):
    unread_count: int


class NotificationMarkReadRequest(BaseModel):
    notification_ids: Optional[List[str]] = None
