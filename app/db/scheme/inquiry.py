from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class InquiryCreate(BaseModel):
    user_id: Optional[int] = None
    inquiry_type: str
    title: str
    content: str


class InquiryAnswer(BaseModel):
    answer: str


class InquiryRead(BaseModel):
    inquiry_id: int
    user_id: Optional[int] = None
    inquiry_type: str
    title: str
    content: str
    answer: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None
    answered_at: Optional[datetime] = None

    class Config:
        from_attributes = True
