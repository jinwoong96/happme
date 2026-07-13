from app.db.database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import JSON, Integer, String, ForeignKey
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from .policy import Policy


class PolicyIncomeRequired(Base):
    __tablename__ = "policy_incomeRequired"

    policy_incom_id: Mapped[int]       = mapped_column(Integer, ForeignKey("policy.policy_id"), primary_key=True)
    plcyNo:          Mapped[str]       = mapped_column(String(50), nullable=False)
    required_fields: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)

    policy: Mapped["Policy"] = relationship("Policy", back_populates="income_required")
