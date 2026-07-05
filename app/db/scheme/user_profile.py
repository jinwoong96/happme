from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class UserProfileCreate(BaseModel):
    user_id: int
    age: Optional[int] = None
    gender: Optional[str] = None
    region: Optional[str] = None
    district: Optional[str] = None
    education: Optional[str] = None
    school_name: Optional[str] = None
    major: Optional[str] = None
    student_status: Optional[str] = None
    graduation_year: Optional[int] = None
    employment_status: Optional[str] = None
    occupation: Optional[str] = None
    job_seeking: bool = False
    career_history: Optional[str] = None
    monthly_income: Optional[int] = None
    household_income_ratio: Optional[int] = None
    household_size: Optional[int] = None
    assets: Optional[int] = None
    marital_status: Optional[str] = None
    disability: bool = False
    veteran: bool = False
    military_status: Optional[str] = None
    startup_interest: bool = False
    business_owner: bool = False
    startup_status: Optional[str] = None
    company_type: Optional[str] = None
    situation: Optional[str] = None
    housing_status: Optional[str] = None
    reason: Optional[str] = None


class UserProfileUpdate(BaseModel):
    age: Optional[int] = None
    gender: Optional[str] = None
    region: Optional[str] = None
    district: Optional[str] = None
    education: Optional[str] = None
    school_name: Optional[str] = None
    major: Optional[str] = None
    student_status: Optional[str] = None
    graduation_year: Optional[int] = None
    employment_status: Optional[str] = None
    occupation: Optional[str] = None
    job_seeking: Optional[bool] = None
    career_history: Optional[str] = None
    monthly_income: Optional[int] = None
    household_income_ratio: Optional[int] = None
    household_size: Optional[int] = None
    assets: Optional[int] = None
    marital_status: Optional[str] = None
    disability: Optional[bool] = None
    veteran: Optional[bool] = None
    military_status: Optional[str] = None
    startup_interest: Optional[bool] = None
    business_owner: Optional[bool] = None
    startup_status: Optional[str] = None
    company_type: Optional[str] = None
    situation: Optional[str] = None
    housing_status: Optional[str] = None
    reason: Optional[str] = None


class UserProfileRead(BaseModel):
    user_id: int
    age: Optional[int] = None
    gender: Optional[str] = None
    region: Optional[str] = None
    district: Optional[str] = None
    education: Optional[str] = None
    school_name: Optional[str] = None
    major: Optional[str] = None
    student_status: Optional[str] = None
    graduation_year: Optional[int] = None
    employment_status: Optional[str] = None
    occupation: Optional[str] = None
    job_seeking: bool = False
    career_history: Optional[str] = None
    monthly_income: Optional[int] = None
    household_income_ratio: Optional[int] = None
    household_size: Optional[int] = None
    assets: Optional[int] = None
    marital_status: Optional[str] = None
    disability: bool = False
    veteran: bool = False
    military_status: Optional[str] = None
    startup_interest: bool = False
    business_owner: bool = False
    startup_status: Optional[str] = None
    company_type: Optional[str] = None
    situation: Optional[str] = None
    housing_status: Optional[str] = None
    reason: Optional[str] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
