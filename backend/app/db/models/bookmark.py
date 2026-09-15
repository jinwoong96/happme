from app.db.database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, Boolean, DateTime, ForeignKey, func, UniqueConstraint, CheckConstraint
from datetime import datetime
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User
    from .policy import Policy
    from .local_program import LocalProgram


class Bookmark(Base):
    __tablename__ = "bookmark"
    __table_args__ = (
        UniqueConstraint("user_id", "policy_id"),
        UniqueConstraint("user_id", "local_program_id"),
        CheckConstraint(
            "policy_id IS NOT NULL OR local_program_id IS NOT NULL",
            name="ck_bookmark_target_required",
        ),
    )

    bookmark_id:      Mapped[int]            = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id:          Mapped[int]            = mapped_column(Integer, ForeignKey("user.user_id"), nullable=False)
    policy_id:        Mapped[Optional[int]]  = mapped_column(Integer, ForeignKey("policy.policy_id"), nullable=True)
    local_program_id: Mapped[Optional[int]]  = mapped_column(Integer, ForeignKey("local_program.local_program_id"), nullable=True)
    alarm_yn:         Mapped[bool]           = mapped_column(Boolean, nullable=False, default=False)
    created_at:       Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=func.now(), nullable=True)

    user:          Mapped["User"]           = relationship("User", back_populates="bookmarks")
    policy:        Mapped[Optional["Policy"]]       = relationship("Policy", back_populates="bookmarks")
    local_program: Mapped[Optional["LocalProgram"]] = relationship("LocalProgram")
