from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class UserTestProfileCreate(BaseModel):
    user_id: int
    birth_date: Optional[date] = None
    gender: Optional[str] = None
    region: Optional[str] = None
    district: Optional[str] = None
    education: Optional[str] = None
    major_category: Optional[str] = None
    employment_status: Optional[str] = None
    sme_employment: bool = False
    marital_status: Optional[str] = None
    disability: bool = False
    basic_livelihood: bool = False
    single_parent: bool = False
    situation: Optional[str] = None


class UserTestProfileRead(UserTestProfileCreate):
    testprofile_id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
