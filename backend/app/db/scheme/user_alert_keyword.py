from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class UserAlertKeywordCreate(BaseModel):
    user_id: Optional[int] = None
    keyword: str = Field(..., min_length=1, max_length=100)


class UserAlertKeywordRead(BaseModel):
    keyword_id: int
    user_id: int
    keyword: str
    is_active: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
