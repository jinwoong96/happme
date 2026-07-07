from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.db.scheme.policy_schedule_event import PolicyScheduleEventRead


class BookmarkCreate(BaseModel):
    user_id: Optional[int] = None
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


class BookmarkCalendarItem(BaseModel):
    bookmark_id: int
    policy_id: int
    plcyNm: str
    sprvsnInstCdNm: Optional[str] = None
    aplyYmd: str
    alarm_yn: bool
    events: list[PolicyScheduleEventRead] = []
    prep_tip: Optional[str] = None
