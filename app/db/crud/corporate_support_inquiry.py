from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.corporate_support_inquiry import CorporateSupportInquiry
from app.db.scheme.corporate_support_inquiry import CorporateSupportInquiryCreate


class CorporateSupportInquiryCrud:

    @staticmethod
    async def create_inquiry(db: AsyncSession, data: CorporateSupportInquiryCreate) -> CorporateSupportInquiry:
        inquiry = CorporateSupportInquiry(**data.model_dump())
        db.add(inquiry)
        await db.flush()
        return inquiry

    @staticmethod
    async def get_inquiry(db: AsyncSession, inquiry_id: int) -> CorporateSupportInquiry | None:
        result = await db.execute(
            select(CorporateSupportInquiry).where(CorporateSupportInquiry.corporate_support_inquiry_id == inquiry_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all(db: AsyncSession) -> list[CorporateSupportInquiry]:
        result = await db.execute(select(CorporateSupportInquiry).order_by(CorporateSupportInquiry.created_at.desc()))
        return list(result.scalars().all())

    @staticmethod
    async def get_by_user(db: AsyncSession, user_id: int) -> list[CorporateSupportInquiry]:
        result = await db.execute(
            select(CorporateSupportInquiry).where(CorporateSupportInquiry.user_id == user_id).order_by(CorporateSupportInquiry.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def answer_inquiry(db: AsyncSession, inquiry: CorporateSupportInquiry, answer: str) -> CorporateSupportInquiry:
        inquiry.answer = answer
        inquiry.status = "ANSWERED"
        inquiry.answered_at = datetime.now()
        await db.flush()
        return inquiry

    @staticmethod
    async def delete_inquiry(db: AsyncSession, inquiry: CorporateSupportInquiry) -> None:
        await db.delete(inquiry)
        await db.flush()
