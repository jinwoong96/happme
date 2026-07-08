from app.db.database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, func
from datetime import datetime
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User


class CorporateSupportInquiry(Base):
    __tablename__ = "corporate_support_inquiry"

    corporate_support_inquiry_id: Mapped[int]         = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id:         Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("user.user_id"), nullable=True)
    company_name:    Mapped[str]           = mapped_column(String(255), nullable=False)
    support_content: Mapped[str]           = mapped_column(Text, nullable=False)
    support_period:  Mapped[str]           = mapped_column(String(100), nullable=False)
    answer:          Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status:          Mapped[str]           = mapped_column(String(20), nullable=False, default="PENDING")
    created_at:      Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=func.now(), nullable=True)
    answered_at:     Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    user: Mapped[Optional["User"]] = relationship("User", back_populates="corporate_support_inquiries")
