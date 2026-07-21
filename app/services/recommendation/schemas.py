from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel


class UserProfileIn(BaseModel):
    """backend의 UserProfileRead와 필드 구조를 맞춘 사용자 프로필 입력 스키마."""

    user_id: int
    birth_date: Optional[date] = None
    age: Optional[int] = None
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


class ScenarioResolveRequest(BaseModel):
    """구조화 질문(Q1 지역이동, Q2 취업 변화) 답변을 diff로 바꿔달라는 요청."""

    region_choice: Literal["지역 쓰기", "지역 이동 안함", "미정"]
    region_text: Optional[str] = None
    employment_choice: Literal["없음", "이직", "퇴사", "창업", "재직", "기타"]
    employment_other: Optional[str] = None


class ScenarioResolveResponse(BaseModel):
    diff: dict
    ambiguous: dict
    notes: list[str]


class IncomeEligibilityRequest(BaseModel):
    """소득 확인 모달에서 사용자가 입력한 답변으로 특정 정책의 지원 가능 여부를 물어보는 요청."""

    plcyNo: str
    answers: dict = {}


class IncomeEligibilityResponse(BaseModel):
    eligible: Optional[bool]
    method: Literal["rule", "llm", "not_found", "unknown_income"]
    reason: str
