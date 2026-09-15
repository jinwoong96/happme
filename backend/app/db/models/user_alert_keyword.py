from app.db.database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, DateTime, Integer, ForeignKey, func, UniqueConstraint
from datetime import datetime
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User


class UserAlertKeyword(Base):
    """지원금 알림 탭 '공고문 알림 받기'로 등록한 자유 텍스트 키워드.
    제목이 아니라 "보증금", "전세보증금 관련"처럼 관심 주제를 자연어로 저장해두고,
    새 공고문이 등록/변경될 때 이 텍스트로 bene_ai 유사도 검색 + 자격 판정을 돌려
    지원 가능한 정책이 있으면 Notification을 만든다."""

    __tablename__ = "user_alert_keyword"
    __table_args__ = (
        UniqueConstraint("user_id", "keyword"),
    )

    keyword_id: Mapped[int]            = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id:    Mapped[int]            = mapped_column(Integer, ForeignKey("user.user_id"), nullable=False)
    keyword:    Mapped[str]            = mapped_column(String(100), nullable=False)
    is_active:  Mapped[bool]           = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=func.now(), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="alert_keywords")
