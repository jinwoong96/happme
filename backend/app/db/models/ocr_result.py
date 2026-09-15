from app.db.database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, Text, Float, String, DateTime, ForeignKey, func
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User
    from .policy import Policy


class OcrResult(Base):
    __tablename__ = "ocr_result"

    ocr_id:         Mapped[int]            = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id:        Mapped[int]            = mapped_column(Integer, ForeignKey("user.user_id"), nullable=False)
    extracted_text: Mapped[str]            = mapped_column(Text, nullable=False)
    created_at:     Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=func.now(), nullable=True)

    user:    Mapped["User"]              = relationship("User", back_populates="ocr_results")
    matches: Mapped[List["OcrResultMatch"]] = relationship("OcrResultMatch", back_populates="ocr_result", cascade="all, delete-orphan")


class OcrResultMatch(Base):
    __tablename__ = "ocr_result_match"

    ocr_id:      Mapped[int]            = mapped_column(Integer, ForeignKey("ocr_result.ocr_id"), primary_key=True)
    policy_id:   Mapped[int]            = mapped_column(Integer, ForeignKey("policy.policy_id"), primary_key=True)
    match_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    match_type:  Mapped[Optional[str]]  = mapped_column(String(20), nullable=True)

    ocr_result: Mapped["OcrResult"] = relationship("OcrResult", back_populates="matches")
    policy:     Mapped["Policy"]    = relationship("Policy", back_populates="ocr_matches")
