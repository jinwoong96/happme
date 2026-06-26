from app.db.database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, JSON, DateTime, ForeignKey, func
from datetime import datetime
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User
    from .policy import Policy


class SimulationResult(Base):
    __tablename__ = "simulation_result"

    result_id:        Mapped[int]            = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id:          Mapped[int]            = mapped_column(Integer, ForeignKey("user.user_id"), nullable=False)
    policy_id:        Mapped[int]            = mapped_column(Integer, ForeignKey("policy.policy_id"), nullable=False)
    simulation_input: Mapped[dict]           = mapped_column(JSON, nullable=False)
    created_at:       Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=func.now(), nullable=True)

    user:   Mapped["User"]   = relationship("User", back_populates="simulation_results")
    policy: Mapped["Policy"] = relationship("Policy", back_populates="simulation_results")
