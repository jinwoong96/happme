from app.db.database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, func
from datetime import datetime
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User


class Inquiry(Base):
    __tablename__ = "inquiry"

    inquiry_id:   Mapped[int]            = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id:      Mapped[Optional[int]]  = mapped_column(Integer, ForeignKey("user.user_id"), nullable=True)
    inquiry_type: Mapped[str]            = mapped_column(String(50), nullable=False)
    title:        Mapped[str]            = mapped_column(String(255), nullable=False)
    content:      Mapped[str]            = mapped_column(Text, nullable=False)
    answer:       Mapped[Optional[str]]  = mapped_column(Text, nullable=True)
    status:       Mapped[str]            = mapped_column(String(20), nullable=False, default="PENDING")
    created_at:   Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=func.now(), nullable=True)
    answered_at:  Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    user: Mapped[Optional["User"]] = relationship("User", back_populates="inquiries")
