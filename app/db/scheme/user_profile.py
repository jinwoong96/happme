from pydantic import BaseModel, computed_field
from datetime import date, datetime
from typing import Optional


class UserProfileCreate(BaseModel):
    user_id: int
    birth_date: Optional[date] = None
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
    birth_date: Optional[date] = None
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
    birth_date: Optional[date] = None
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

    @computed_field
    @property
    def age(self) -> Optional[int]:
        """생년월일(만 나이) 기준으로 계산합니다. 저장된 값이 아니라 조회 시점마다 계산됩니다."""
        if not self.birth_date:
            return None
        today = date.today()
        age = today.year - self.birth_date.year
        if (today.month, today.day) < (self.birth_date.month, self.birth_date.day):
            age -= 1
        return age
