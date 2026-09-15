from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class NoticeCreate(BaseModel):
    admin_id: int
    title: str
    content: str
    is_pinned: bool = False


class NoticeUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    is_pinned: Optional[bool] = None


class NoticeRead(BaseModel):
    notice_id: int
    admin_id: int
    title: str
    content: str
    is_pinned: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
