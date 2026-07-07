from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class CorporateSupportInquiryCreate(BaseModel):
    user_id: Optional[int] = None
    company_name: str
    support_content: str
    support_period: str


class CorporateSupportInquiryAnswer(BaseModel):
    answer: str


class CorporateSupportInquiryRead(BaseModel):
    corporate_support_inquiry_id: int
    user_id: Optional[int] = None
    company_name: str
    support_content: str
    support_period: str
    answer: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None
    answered_at: Optional[datetime] = None

    class Config:
        from_attributes = True
