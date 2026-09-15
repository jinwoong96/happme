from app.db.database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, Integer, Boolean, DateTime, ForeignKey, func
from datetime import datetime
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User
    from .policy import Policy


class Notification(Base):
    __tablename__ = "notification"

    notification_id: Mapped[int]            = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id:         Mapped[int]            = mapped_column(Integer, ForeignKey("user.user_id"), nullable=False)
    policy_id:       Mapped[Optional[int]]  = mapped_column(Integer, ForeignKey("policy.policy_id"), nullable=True)
    notify_type:     Mapped[str]            = mapped_column(String(20), nullable=False)
    title:           Mapped[str]            = mapped_column(String(255), nullable=False)
    content:         Mapped[Optional[str]]  = mapped_column(Text, nullable=True)
    is_read:         Mapped[bool]           = mapped_column(Boolean, nullable=False, default=False)
    created_at:      Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=func.now(), nullable=True)

    user:   Mapped["User"]            = relationship("User", back_populates="notifications")
    policy: Mapped[Optional["Policy"]] = relationship("Policy", back_populates="notifications")
