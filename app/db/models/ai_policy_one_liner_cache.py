from sqlalchemy import ForeignKey, Integer, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class AiPolicyOneLinerCache(Base):
    """
    bene_ai가 raw pymysql로 읽고 쓰는 정책 한 줄 요약 캐시.
    policy_id 단위라 매칭 조합/이미지와 무관하게 재사용된다.
    이 모델은 create_all로 테이블만 생성해주는 용도.
    """
    __tablename__ = "ai_policy_one_liner_cache"

    policy_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("policy.policy_id"), primary_key=True
    )
    one_liner: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped["DateTime"] = mapped_column(DateTime, server_default=func.now())