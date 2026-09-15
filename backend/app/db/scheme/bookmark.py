from pydantic import BaseModel, model_validator
from datetime import datetime
from typing import Optional
from app.db.scheme.policy_schedule_event import PolicyScheduleEventRead


class BookmarkCreate(BaseModel):
    user_id: Optional[int] = None
    policy_id: Optional[int] = None
    local_program_id: Optional[int] = None
    alarm_yn: bool = False

    @model_validator(mode="after")
    def check_target(self):
        if not self.policy_id and not self.local_program_id:
            raise ValueError("policy_id 또는 local_program_id 중 하나는 필요합니다.")
        if self.policy_id and self.local_program_id:
            raise ValueError("policy_id와 local_program_id는 동시에 넣을 수 없습니다.")
        return self


class BookmarkUpdate(BaseModel):
    alarm_yn: Optional[bool] = None


class BookmarkRead(BaseModel):
    bookmark_id: int
    user_id: int
    policy_id: Optional[int] = None
    local_program_id: Optional[int] = None
    alarm_yn: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BookmarkCalendarItem(BaseModel):
    bookmark_id: int
    policy_id: Optional[int] = None
    local_program_id: Optional[int] = None
    plcyNm: str
    sprvsnInstCdNm: Optional[str] = None
    aplyYmd: str
    alarm_yn: bool
    events: list[PolicyScheduleEventRead] = []
    prep_tip: Optional[str] = None
    applyUrl: Optional[str] = None
