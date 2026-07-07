from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.db.crud.ad_partnership_inquiry import AdPartnershipInquiryCrud
from app.db.scheme.ad_partnership_inquiry import AdPartnershipInquiryCreate
from app.db.models.ad_partnership_inquiry import AdPartnershipInquiry


class AdPartnershipInquiryService:

    @staticmethod
    async def create_inquiry_svc(db: AsyncSession, data: AdPartnershipInquiryCreate) -> AdPartnershipInquiry:
        try:
            inquiry = await AdPartnershipInquiryCrud.create_inquiry(db, data)
            await db.commit()
            await db.refresh(inquiry)
            return inquiry
        except Exception:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="광고제휴 문의 생성에 실패했습니다.")

    @staticmethod
    async def get_inquiry_svc(db: AsyncSession, inquiry_id: int) -> AdPartnershipInquiry:
        inquiry = await AdPartnershipInquiryCrud.get_inquiry(db, inquiry_id)
        if not inquiry:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="문의를 찾을 수 없습니다.")
        return inquiry

    @staticmethod
    async def get_all_inquiries_svc(db: AsyncSession) -> list[AdPartnershipInquiry]:
        return await AdPartnershipInquiryCrud.get_all(db)

    @staticmethod
    async def get_my_inquiries_svc(db: AsyncSession, user_id: int) -> list[AdPartnershipInquiry]:
        return await AdPartnershipInquiryCrud.get_by_user(db, user_id)

    @staticmethod
    async def answer_inquiry_svc(db: AsyncSession, inquiry_id: int, answer: str) -> AdPartnershipInquiry:
        inquiry = await AdPartnershipInquiryCrud.get_inquiry(db, inquiry_id)
        if not inquiry:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="문의를 찾을 수 없습니다.")
        try:
            updated = await AdPartnershipInquiryCrud.answer_inquiry(db, inquiry, answer)
            await db.commit()
            await db.refresh(updated)
            return updated
        except Exception:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="답변 등록에 실패했습니다.")

    @staticmethod
    async def delete_inquiry_svc(db: AsyncSession, inquiry_id: int) -> dict:
        inquiry = await AdPartnershipInquiryCrud.get_inquiry(db, inquiry_id)
        if not inquiry:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="문의를 찾을 수 없습니다.")
        try:
            await AdPartnershipInquiryCrud.delete_inquiry(db, inquiry)
            await db.commit()
            return {"message": f"ad_partnership_inquiry_id '{inquiry_id}' 삭제 완료"}
        except Exception:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="문의 삭제에 실패했습니다.")
