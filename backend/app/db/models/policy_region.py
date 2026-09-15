from app.db.database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, ForeignKey
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .policy import Policy


class PolicyRegion(Base):
    __tablename__ = "policy_region"

    policy_id: Mapped[int] = mapped_column(Integer, ForeignKey("policy.policy_id"), primary_key=True)
    zip_code:  Mapped[str] = mapped_column(String(20), primary_key=True)

    policy: Mapped["Policy"] = relationship("Policy", back_populates="regions")
