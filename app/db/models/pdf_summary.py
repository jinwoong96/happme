from app.db.database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, Text, Float, String, DateTime, ForeignKey, func
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User
    from .policy import Policy


class PdfSummary(Base):
    __tablename__ = "pdf_summary"

    pdf_id:       Mapped[int]            = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id:      Mapped[int]            = mapped_column(Integer, ForeignKey("user.user_id"), nullable=False)
    summary_text: Mapped[str]            = mapped_column(Text, nullable=False)
    created_at:   Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=func.now(), nullable=True)

    user:    Mapped["User"]                 = relationship("User", back_populates="pdf_summaries")
    matches: Mapped[List["PdfSummaryMatch"]] = relationship("PdfSummaryMatch", back_populates="pdf_summary", cascade="all, delete-orphan")


class PdfSummaryMatch(Base):
    __tablename__ = "pdf_summary_match"

    pdf_id:      Mapped[int]             = mapped_column(Integer, ForeignKey("pdf_summary.pdf_id"), primary_key=True)
    policy_id:   Mapped[int]             = mapped_column(Integer, ForeignKey("policy.policy_id"), primary_key=True)
    match_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    match_type:  Mapped[Optional[str]]   = mapped_column(String(20), nullable=True)

    pdf_summary: Mapped["PdfSummary"] = relationship("PdfSummary", back_populates="matches")
    policy:      Mapped["Policy"]     = relationship("Policy", back_populates="pdf_matches")
