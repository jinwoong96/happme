from app.db.database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Text, Integer, DateTime, ForeignKey, func
from datetime import datetime
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .policy import Policy


class PolicyAiTip(Base):
    __tablename__ = "policy_ai_tip"

    policy_id:    Mapped[int]            = mapped_column(Integer, ForeignKey("policy.policy_id"), primary_key=True)
    tip:          Mapped[str]            = mapped_column(Text, nullable=False)
    generated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=func.now(), nullable=True)

    policy: Mapped["Policy"] = relationship("Policy", back_populates="ai_tip")
