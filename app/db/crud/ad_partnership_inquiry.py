from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.ad_partnership_inquiry import AdPartnershipInquiry
from app.db.scheme.ad_partnership_inquiry import AdPartnershipInquiryCreate


class AdPartnershipInquiryCrud:

    @staticmethod
    async def create_inquiry(db: AsyncSession, data: AdPartnershipInquiryCreate) -> AdPartnershipInquiry:
        inquiry = AdPartnershipInquiry(**data.model_dump())
        db.add(inquiry)
        await db.flush()
        return inquiry

    @staticmethod
    async def get_inquiry(db: AsyncSession, inquiry_id: int) -> AdPartnershipInquiry | None:
        result = await db.execute(
            select(AdPartnershipInquiry).where(AdPartnershipInquiry.ad_partnership_inquiry_id == inquiry_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all(db: AsyncSession) -> list[AdPartnershipInquiry]:
        result = await db.execute(select(AdPartnershipInquiry).order_by(AdPartnershipInquiry.created_at.desc()))
        return list(result.scalars().all())

    @staticmethod
    async def get_by_user(db: AsyncSession, user_id: int) -> list[AdPartnershipInquiry]:
        result = await db.execute(
            select(AdPartnershipInquiry).where(AdPartnershipInquiry.user_id == user_id).order_by(AdPartnershipInquiry.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def answer_inquiry(db: AsyncSession, inquiry: AdPartnershipInquiry, answer: str) -> AdPartnershipInquiry:
        inquiry.answer = answer
        inquiry.status = "ANSWERED"
        inquiry.answered_at = datetime.now()
        await db.flush()
        return inquiry

    @staticmethod
    async def delete_inquiry(db: AsyncSession, inquiry: AdPartnershipInquiry) -> None:
        await db.delete(inquiry)
        await db.flush()
