from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.db.crud.pdf_summary import PdfSummaryCrud
from app.db.crud.user import UserCrud
from app.db.scheme.pdf_summary import PdfSummaryCreate, PdfMatchCreate
from app.db.models.pdf_summary import PdfSummary, PdfSummaryMatch


class PdfSummaryService:

    @staticmethod
    async def create_pdf_svc(db: AsyncSession, data: PdfSummaryCreate) -> PdfSummary:
        if not await UserCrud.get_user(db, data.user_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="유저를 찾을 수 없습니다.")
        try:
            pdf = await PdfSummaryCrud.create_pdf(db, data)
            await db.commit()
            await db.refresh(pdf)
            return pdf
        except Exception:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="PDF 요약 저장에 실패했습니다.")

    @staticmethod
    async def get_pdf_svc(db: AsyncSession, pdf_id: int) -> PdfSummary:
        pdf = await PdfSummaryCrud.get_pdf(db, pdf_id)
        if not pdf:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PDF 요약을 찾을 수 없습니다.")
        return pdf

    @staticmethod
    async def get_by_user_svc(db: AsyncSession, user_id: int) -> list[PdfSummary]:
        if not await UserCrud.get_user(db, user_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="유저를 찾을 수 없습니다.")
        return await PdfSummaryCrud.get_by_user(db, user_id)

    @staticmethod
    async def add_match_svc(db: AsyncSession, data: PdfMatchCreate) -> PdfSummaryMatch:
        try:
            match = await PdfSummaryCrud.add_match(db, data)
            await db.commit()
            await db.refresh(match)
            return match
        except Exception:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="PDF 매칭 추가에 실패했습니다.")

    @staticmethod
    async def delete_pdf_svc(db: AsyncSession, pdf_id: int) -> dict:
        pdf = await PdfSummaryCrud.get_pdf(db, pdf_id)
        if not pdf:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PDF 요약을 찾을 수 없습니다.")
        try:
            await PdfSummaryCrud.delete_pdf(db, pdf)
            await db.commit()
            return {"message": f"pdf_id '{pdf_id}' 삭제 완료"}
        except Exception:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="PDF 요약 삭제에 실패했습니다.")
