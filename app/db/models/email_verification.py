from app.db.database import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Boolean, DateTime, Integer, func
from datetime import datetime
from typing import Optional


class EmailVerification(Base):
    __tablename__ = "email_verification"

    id:         Mapped[int]            = mapped_column(Integer, primary_key=True, autoincrement=True)
    email:      Mapped[str]            = mapped_column(String(100), nullable=False, index=True)
    code:       Mapped[str]            = mapped_column(String(6), nullable=False)
    is_verified: Mapped[bool]          = mapped_column(Boolean, nullable=False, default=False)
    expires_at: Mapped[datetime]       = mapped_column(DateTime, nullable=False)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=func.now(), nullable=True)