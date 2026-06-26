from app.db.database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Boolean, BigInteger, Text, DateTime, ForeignKey, func
from datetime import datetime
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User


class UserProfile(Base):
    __tablename__ = "user_profile"

    user_id:                Mapped[int]            = mapped_column(Integer, ForeignKey("user.user_id"), primary_key=True)
    age:                    Mapped[Optional[int]]   = mapped_column(Integer, nullable=True)
    gender:                 Mapped[Optional[str]]   = mapped_column(String(10), nullable=True)
    region:                 Mapped[Optional[str]]   = mapped_column(String(50), nullable=True)
    district:               Mapped[Optional[str]]   = mapped_column(String(50), nullable=True)
    education:              Mapped[Optional[str]]   = mapped_column(String(50), nullable=True)
    school_name:            Mapped[Optional[str]]   = mapped_column(String(100), nullable=True)
    major:                  Mapped[Optional[str]]   = mapped_column(String(100), nullable=True)
    student_status:         Mapped[Optional[str]]   = mapped_column(String(50), nullable=True)
    graduation_year:        Mapped[Optional[int]]   = mapped_column(Integer, nullable=True)
    employment_status:      Mapped[Optional[str]]   = mapped_column(String(50), nullable=True)
    occupation:             Mapped[Optional[str]]   = mapped_column(String(50), nullable=True)
    job_seeking:            Mapped[bool]            = mapped_column(Boolean, nullable=False, default=False)
    career_history:         Mapped[Optional[str]]   = mapped_column(Text, nullable=True)
    monthly_income:         Mapped[Optional[int]]   = mapped_column(BigInteger, nullable=True)
    household_income_ratio: Mapped[Optional[int]]   = mapped_column(Integer, nullable=True)
    household_size:         Mapped[Optional[int]]   = mapped_column(Integer, nullable=True)
    assets:                 Mapped[Optional[int]]   = mapped_column(BigInteger, nullable=True)
    marital_status:         Mapped[Optional[str]]   = mapped_column(String(20), nullable=True)
    disability:             Mapped[bool]            = mapped_column(Boolean, nullable=False, default=False)
    veteran:                Mapped[bool]            = mapped_column(Boolean, nullable=False, default=False)
    military_status:        Mapped[Optional[str]]   = mapped_column(String(20), nullable=True)
    startup_interest:       Mapped[bool]            = mapped_column(Boolean, nullable=False, default=False)
    business_owner:         Mapped[bool]            = mapped_column(Boolean, nullable=False, default=False)
    startup_status:         Mapped[Optional[str]]   = mapped_column(String(50), nullable=True)
    situation:              Mapped[Optional[str]]   = mapped_column(Text, nullable=True)
    housing_status:         Mapped[Optional[str]]   = mapped_column(String(50), nullable=True)
    reason:                 Mapped[Optional[str]]   = mapped_column(Text, nullable=True)
    updated_at:             Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="profile")
