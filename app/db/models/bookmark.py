from app.db.database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, Boolean, DateTime, ForeignKey, func, UniqueConstraint
from datetime import datetime
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User
    from .policy import Policy


class Bookmark(Base):
    __tablename__ = "bookmark"
    __table_args__ = (UniqueConstraint("user_id", "policy_id"),)

    bookmark_id: Mapped[int]            = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id:     Mapped[int]            = mapped_column(Integer, ForeignKey("user.user_id"), nullable=False)
    policy_id:   Mapped[int]            = mapped_column(Integer, ForeignKey("policy.policy_id"), nullable=False)
    alarm_yn:    Mapped[bool]           = mapped_column(Boolean, nullable=False, default=False)
    created_at:  Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=func.now(), nullable=True)

    user:   Mapped["User"]   = relationship("User", back_populates="bookmarks")
    policy: Mapped["Policy"] = relationship("Policy", back_populates="bookmarks")
