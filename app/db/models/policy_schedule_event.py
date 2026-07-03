from app.db.database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, func, UniqueConstraint
from datetime import datetime
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .policy import Policy


class PolicyScheduleEvent(Base):
    __tablename__ = "policy_schedule_event"
    __table_args__ = (UniqueConstraint("policy_id", "event_type", "event_date"),)

    event_id:   Mapped[int]            = mapped_column(Integer, primary_key=True, autoincrement=True)
    policy_id:  Mapped[int]            = mapped_column(Integer, ForeignKey("policy.policy_id"), nullable=False)
    event_type: Mapped[str]            = mapped_column(String(20), nullable=False)
    event_date: Mapped[str]            = mapped_column(String(50), nullable=False)
    raw_text:   Mapped[str]            = mapped_column(Text, nullable=False)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=func.now(), nullable=True)

    policy: Mapped["Policy"] = relationship("Policy", back_populates="schedule_events")
