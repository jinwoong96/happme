from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.db.models.pdf_summary import PdfSummary, PdfSummaryMatch
from app.db.scheme.pdf_summary import PdfSummaryCreate, PdfMatchCreate


class PdfSummaryCrud:
    """PDF/텍스트/URL 공고문 매칭 결과(pdf_summary)와 매칭된 정책(pdf_summary_match)
    조회/생성/삭제."""

    @staticmethod
    async def create_pdf(db: AsyncSession, data: PdfSummaryCreate) -> PdfSummary:
        pdf = PdfSummary(**data.model_dump())
        db.add(pdf)
        await db.flush()
        return pdf

    @staticmethod
    async def get_pdf(db: AsyncSession, pdf_id: int) -> PdfSummary | None:
        result = await db.execute(
            select(PdfSummary).options(selectinload(PdfSummary.matches)).where(PdfSummary.pdf_id == pdf_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_user(db: AsyncSession, user_id: int) -> list[PdfSummary]:
        result = await db.execute(
            select(PdfSummary).options(selectinload(PdfSummary.matches))
            .where(PdfSummary.user_id == user_id)
            .order_by(PdfSummary.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def add_match(db: AsyncSession, data: PdfMatchCreate) -> PdfSummaryMatch:
        match = PdfSummaryMatch(**data.model_dump())
        db.add(match)
        await db.flush()
        return match

    @staticmethod
    async def delete_pdf(db: AsyncSession, pdf: PdfSummary) -> None:
        await db.delete(pdf)
        await db.flush()
