from app.db.database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, Integer, Boolean, DateTime, ForeignKey, func
from datetime import datetime
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User


class Notice(Base):
    __tablename__ = "notice"

    notice_id:  Mapped[int]            = mapped_column(Integer, primary_key=True, autoincrement=True)
    admin_id:   Mapped[int]            = mapped_column(Integer, ForeignKey("user.user_id"), nullable=False)
    title:      Mapped[str]            = mapped_column(String(255), nullable=False)
    content:    Mapped[str]            = mapped_column(Text, nullable=False)
    is_pinned:  Mapped[bool]           = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=func.now(), nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)

    admin: Mapped["User"] = relationship("User", back_populates="notices")
