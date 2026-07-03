from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class PolicyScheduleEventRead(BaseModel):
    event_type: str
    event_date: str
    raw_text: str

    class Config:
        from_attributes = True


class PolicyAiTipRead(BaseModel):
    tip: str
    generated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
