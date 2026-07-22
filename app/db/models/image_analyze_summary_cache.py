from sqlalchemy import String, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class ImageAnalyzeSummaryCache(Base):
    """
    bene_ai가 raw pymysql로 읽고 쓰는 정책 "조합" 요약 캐시.
    이미지는 달라도 매칭된 policy_id 조합(정렬 후 ','로 join)이 같으면
    LLM 종합요약을 재사용한다. 이 모델은 create_all로 테이블만 생성해주는 용도.
    """
    __tablename__ = "image_analyze_summary_cache"

    combo_key: Mapped[str] = mapped_column(String(255), primary_key=True)
    summary_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped["DateTime"] = mapped_column(DateTime, server_default=func.now())
    last_used_at: Mapped["DateTime"] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )