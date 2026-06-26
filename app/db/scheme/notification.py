from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class NotificationCreate(BaseModel):
    user_id: int
    policy_id: Optional[int] = None
    notify_type: str
    title: str
    content: Optional[str] = None


class NotificationRead(BaseModel):
    notification_id: int
    user_id: int
    policy_id: Optional[int] = None
    notify_type: str
    title: str
    content: Optional[str] = None
    is_read: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
