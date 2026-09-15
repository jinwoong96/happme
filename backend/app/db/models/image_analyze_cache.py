from sqlalchemy import String, JSON, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class ImageAnalyzeCache(Base):
    """
    bene_ai가 raw pymysql로 읽고 쓰는 image_analyze 전체 파이프라인 결과 캐시.
    완전히 동일한 이미지(sha256)가 재업로드되면 detection/OCR/search/LLM 전체를 스킵.
    이 모델은 create_all로 테이블만 생성해주는 용도이며, 실제 read/write는 bene_ai가 담당한다.
    """
    __tablename__ = "image_analyze_cache"

    image_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    result_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped["DateTime"] = mapped_column(DateTime, server_default=func.now())
    last_used_at: Mapped["DateTime"] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )