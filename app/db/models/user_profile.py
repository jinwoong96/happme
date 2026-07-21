from app.db.database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Boolean, BigInteger, Text, DateTime, Date, ForeignKey, func
from datetime import datetime, date
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User


class UserProfile(Base):
    __tablename__ = "user_profile"

    user_id:                Mapped[int]            = mapped_column(Integer, ForeignKey("user.user_id"), primary_key=True)
    birth_date:             Mapped[Optional[date]]  = mapped_column(Date, nullable=True)
    gender:                 Mapped[Optional[str]]   = mapped_column(String(10), nullable=True)
    region:                 Mapped[Optional[str]]   = mapped_column(String(50), nullable=True)
    district:               Mapped[Optional[str]]   = mapped_column(String(50), nullable=True)
    education:              Mapped[Optional[str]]   = mapped_column(String(50), nullable=True)
    major_category:         Mapped[Optional[str]]   = mapped_column(String(50), nullable=True)
    employment_status:      Mapped[Optional[str]]   = mapped_column(String(50), nullable=True)
    sme_employment:         Mapped[bool]            = mapped_column(Boolean, nullable=False, default=False)
    marital_status:         Mapped[Optional[str]]   = mapped_column(String(20), nullable=True)
    disability:             Mapped[bool]            = mapped_column(Boolean, nullable=False, default=False)
    basic_livelihood:       Mapped[bool]            = mapped_column(Boolean, nullable=False, default=False)
    single_parent:          Mapped[bool]            = mapped_column(Boolean, nullable=False, default=False)
    situation:              Mapped[Optional[str]]   = mapped_column(Text, nullable=True)
    updated_at:             Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="profile")
