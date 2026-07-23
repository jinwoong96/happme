from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.db.crud.corporate_support_inquiry import CorporateSupportInquiryCrud
from app.db.scheme.corporate_support_inquiry import CorporateSupportInquiryCreate
from app.db.models.corporate_support_inquiry import CorporateSupportInquiry


class CorporateSupportInquiryService:
    """기업지원금 제휴 문의 생성/조회/답변/삭제."""

    @staticmethod
    async def create_inquiry_svc(db: AsyncSession, data: CorporateSupportInquiryCreate) -> CorporateSupportInquiry:
        try:
            inquiry = await CorporateSupportInquiryCrud.create_inquiry(db, data)
            await db.commit()
            await db.refresh(inquiry)
            return inquiry
        except Exception:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="기업지원금 제휴 문의 생성에 실패했습니다.")

    @staticmethod
    async def get_inquiry_svc(db: AsyncSession, inquiry_id: int) -> CorporateSupportInquiry:
        inquiry = await CorporateSupportInquiryCrud.get_inquiry(db, inquiry_id)
        if not inquiry:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="문의를 찾을 수 없습니다.")
        return inquiry

    @staticmethod
    async def get_all_inquiries_svc(db: AsyncSession) -> list[CorporateSupportInquiry]:
        return await CorporateSupportInquiryCrud.get_all(db)

    @staticmethod
    async def get_my_inquiries_svc(db: AsyncSession, user_id: int) -> list[CorporateSupportInquiry]:
        return await CorporateSupportInquiryCrud.get_by_user(db, user_id)

    @staticmethod
    async def answer_inquiry_svc(db: AsyncSession, inquiry_id: int, answer: str) -> CorporateSupportInquiry:
        inquiry = await CorporateSupportInquiryCrud.get_inquiry(db, inquiry_id)
        if not inquiry:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="문의를 찾을 수 없습니다.")
        try:
            updated = await CorporateSupportInquiryCrud.answer_inquiry(db, inquiry, answer)
            await db.commit()
            await db.refresh(updated)
            return updated
        except Exception:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="답변 등록에 실패했습니다.")

    @staticmethod
    async def delete_inquiry_svc(db: AsyncSession, inquiry_id: int) -> dict:
        inquiry = await CorporateSupportInquiryCrud.get_inquiry(db, inquiry_id)
        if not inquiry:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="문의를 찾을 수 없습니다.")
        try:
            await CorporateSupportInquiryCrud.delete_inquiry(db, inquiry)
            await db.commit()
            return {"message": f"corporate_support_inquiry_id '{inquiry_id}' 삭제 완료"}
        except Exception:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="문의 삭제에 실패했습니다.")
