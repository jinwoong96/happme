from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.db.models.ocr_result import OcrResult, OcrResultMatch
from app.db.scheme.ocr_result import OcrResultCreate, OcrMatchCreate


class OcrResultCrud:
    """이미지(공고문) OCR 분석 결과(ocr_result)와 매칭된 정책(ocr_result_match) 조회/생성/삭제."""

    @staticmethod
    async def create_ocr(db: AsyncSession, data: OcrResultCreate) -> OcrResult:
        ocr = OcrResult(**data.model_dump())
        db.add(ocr)
        await db.flush()
        return ocr

    @staticmethod
    async def get_ocr(db: AsyncSession, ocr_id: int) -> OcrResult | None:
        result = await db.execute(
            select(OcrResult).options(selectinload(OcrResult.matches)).where(OcrResult.ocr_id == ocr_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_user(db: AsyncSession, user_id: int) -> list[OcrResult]:
        result = await db.execute(
            select(OcrResult).options(selectinload(OcrResult.matches))
            .where(OcrResult.user_id == user_id)
            .order_by(OcrResult.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def add_match(db: AsyncSession, data: OcrMatchCreate) -> OcrResultMatch:
        match = OcrResultMatch(**data.model_dump())
        db.add(match)
        await db.flush()
        return match

    @staticmethod
    async def delete_ocr(db: AsyncSession, ocr: OcrResult) -> None:
        await db.delete(ocr)
        await db.flush()
