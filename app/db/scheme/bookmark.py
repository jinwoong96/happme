from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class BookmarkCreate(BaseModel):
    user_id: int
    policy_id: int
    alarm_yn: bool = False


class BookmarkUpdate(BaseModel):
    alarm_yn: Optional[bool] = None


class BookmarkRead(BaseModel):
    bookmark_id: int
    user_id: int
    policy_id: int
    alarm_yn: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
