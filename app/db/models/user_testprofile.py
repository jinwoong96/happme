from app.db.database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Boolean, Text, DateTime, Date, ForeignKey, func
from datetime import datetime, date
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User


class UserTestProfile(Base):
    """
    Q1(지역이동)/Q2(취업 변화) 시뮬레이션 답변을 실제 user_profile에 병합한 스냅샷.
    실제 user_profile은 건드리지 않고, 컬럼 구조를 그대로 복제해 what-if 프로필을 저장한다.
    AI 추천은 이 테이블에 저장된 값을 기준으로 수행한다.
    """

    __tablename__ = "user_testprofile"

    testprofile_id:         Mapped[int]            = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id:                Mapped[int]            = mapped_column(Integer, ForeignKey("user.user_id"), nullable=False)

    birth_date:             Mapped[Optional[date]]  = mapped_column(Date, nullable=True)
    gender:                 Mapped[Optional[str]]   = mapped_column(String(10), nullable=True)
    region:                 Mapped[Optional[str]]   = mapped_column(String(50), nullable=True)
    district:               Mapped[Optional[str]]   = mapped_column(String(50), nullable=True)
    education:              Mapped[Optional[str]]   = mapped_column(String(50), nullable=True)
    school_name:            Mapped[Optional[str]]   = mapped_column(String(100), nullable=True)
    major:                  Mapped[Optional[str]]   = mapped_column(String(100), nullable=True)
    major_category:         Mapped[Optional[str]]   = mapped_column(String(50), nullable=True)
    student_status:         Mapped[Optional[str]]   = mapped_column(String(50), nullable=True)
    graduation_year:        Mapped[Optional[int]]   = mapped_column(Integer, nullable=True)
    employment_status:      Mapped[Optional[str]]   = mapped_column(String(50), nullable=True)
    occupation:             Mapped[Optional[str]]   = mapped_column(String(50), nullable=True)
    job_seeking:            Mapped[bool]            = mapped_column(Boolean, nullable=False, default=False)
    career_history:         Mapped[Optional[str]]   = mapped_column(Text, nullable=True)
    marital_status:         Mapped[Optional[str]]   = mapped_column(String(20), nullable=True)
    disability:             Mapped[bool]            = mapped_column(Boolean, nullable=False, default=False)
    basic_livelihood:       Mapped[bool]            = mapped_column(Boolean, nullable=False, default=False)
    single_parent:          Mapped[bool]            = mapped_column(Boolean, nullable=False, default=False)
    startup_interest:       Mapped[bool]            = mapped_column(Boolean, nullable=False, default=False)
    business_owner:         Mapped[bool]            = mapped_column(Boolean, nullable=False, default=False)
    startup_status:         Mapped[Optional[str]]   = mapped_column(String(50), nullable=True)
    company_type:           Mapped[Optional[str]]   = mapped_column(String(50), nullable=True)
    situation:              Mapped[Optional[str]]   = mapped_column(Text, nullable=True)
    housing_status:         Mapped[Optional[str]]   = mapped_column(String(50), nullable=True)
    reason:                 Mapped[Optional[str]]   = mapped_column(Text, nullable=True)

    created_at:             Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=func.now(), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="test_profiles")
