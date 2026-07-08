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
    school_name: Optional[str] = None
    major: Optional[str] = None
    major_category: Optional[str] = None
    student_status: Optional[str] = None
    graduation_year: Optional[int] = None
    employment_status: Optional[str] = None
    occupation: Optional[str] = None
    job_seeking: bool = False
    career_history: Optional[str] = None
    marital_status: Optional[str] = None
    disability: bool = False
    basic_livelihood: bool = False
    single_parent: bool = False
    startup_interest: bool = False
    business_owner: bool = False
    startup_status: Optional[str] = None
    company_type: Optional[str] = None
    situation: Optional[str] = None
    housing_status: Optional[str] = None
    reason: Optional[str] = None


class UserTestProfileRead(UserTestProfileCreate):
    testprofile_id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
