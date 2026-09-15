from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.db.crud.inquiry import InquiryCrud
from app.db.crud.notification import NotificationCrud
from app.db.scheme.inquiry import InquiryCreate
from app.db.scheme.notification import NotificationCreate
from app.db.models.inquiry import Inquiry


class InquiryService:
    """일반 문의 생성/조회/답변/삭제."""

    @staticmethod
    async def create_inquiry_svc(db: AsyncSession, data: InquiryCreate) -> Inquiry:
        try:
            inquiry = await InquiryCrud.create_inquiry(db, data)
            await db.commit()
            await db.refresh(inquiry)
            return inquiry
        except Exception:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="문의 생성에 실패했습니다.")

    @staticmethod
    async def get_inquiry_svc(db: AsyncSession, inquiry_id: int) -> Inquiry:
        inquiry = await InquiryCrud.get_inquiry(db, inquiry_id)
        if not inquiry:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="문의를 찾을 수 없습니다.")
        return inquiry

    @staticmethod
    async def get_all_inquiries_svc(db: AsyncSession) -> list[Inquiry]:
        return await InquiryCrud.get_all(db)

    @staticmethod
    async def get_my_inquiries_svc(db: AsyncSession, user_id: int) -> list[Inquiry]:
        return await InquiryCrud.get_by_user(db, user_id)

    @staticmethod
    async def answer_inquiry_svc(db: AsyncSession, inquiry_id: int, answer: str) -> Inquiry:
        """문의에 답변을 등록하고, 작성자가 있으면(비로그인 문의가 아니면) 답변 알림도 함께 만든다."""
        inquiry = await InquiryCrud.get_inquiry(db, inquiry_id)
        if not inquiry:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="문의를 찾을 수 없습니다.")
        try:
            updated = await InquiryCrud.answer_inquiry(db, inquiry, answer)
            if updated.user_id is not None:
                await NotificationCrud.create_notification(db, NotificationCreate(
                    user_id=updated.user_id,
                    notify_type="INQUIRY_ANSWER",
                    title="문의하신 내용에 답변이 등록되었습니다",
                    content=answer,
                ))
            await db.commit()
            await db.refresh(updated)
            return updated
        except Exception:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="답변 등록에 실패했습니다.")

    @staticmethod
    async def delete_inquiry_svc(db: AsyncSession, inquiry_id: int) -> dict:
        inquiry = await InquiryCrud.get_inquiry(db, inquiry_id)
        if not inquiry:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="문의를 찾을 수 없습니다.")
        try:
            await InquiryCrud.delete_inquiry(db, inquiry)
            await db.commit()
            return {"message": f"inquiry_id '{inquiry_id}' 삭제 완료"}
        except Exception:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="문의 삭제에 실패했습니다.")
