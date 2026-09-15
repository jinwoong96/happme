from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class AdPartnershipInquiryCreate(BaseModel):
    user_id: Optional[int] = None
    ad_name: str
    company_name: str
    target_product: str
    content: str


class AdPartnershipInquiryAnswer(BaseModel):
    answer: str


class AdPartnershipInquiryRead(BaseModel):
    ad_partnership_inquiry_id: int
    user_id: Optional[int] = None
    ad_name: str
    company_name: str
    target_product: str
    content: str
    answer: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None
    answered_at: Optional[datetime] = None

    class Config:
        from_attributes = True
