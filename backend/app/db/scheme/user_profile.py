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
    major_category: Optional[str] = None
    employment_status: Optional[str] = None
    sme_employment: bool = False  # 중소기업 재직 여부
    marital_status: Optional[str] = None
    disability: bool = False
    basic_livelihood: bool = False
    single_parent: bool = False
    situation: Optional[str] = None


class UserProfileUpdate(BaseModel):
    birth_date: Optional[date] = None
    gender: Optional[str] = None
    region: Optional[str] = None
    district: Optional[str] = None
    education: Optional[str] = None
    major_category: Optional[str] = None
    employment_status: Optional[str] = None
    sme_employment: Optional[bool] = None  # 중소기업 재직 여부
    marital_status: Optional[str] = None
    disability: Optional[bool] = None
    basic_livelihood: Optional[bool] = None
    single_parent: Optional[bool] = None
    situation: Optional[str] = None


class UserProfileRead(BaseModel):
    user_id: int
    birth_date: Optional[date] = None
    gender: Optional[str] = None
    region: Optional[str] = None
    district: Optional[str] = None
    education: Optional[str] = None
    major_category: Optional[str] = None
    employment_status: Optional[str] = None
    sme_employment: bool = False  # 중소기업 재직 여부
    marital_status: Optional[str] = None
    disability: bool = False
    basic_livelihood: bool = False
    single_parent: bool = False
    situation: Optional[str] = None
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
