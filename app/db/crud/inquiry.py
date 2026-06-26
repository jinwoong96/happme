from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.inquiry import Inquiry
from app.db.scheme.inquiry import InquiryCreate


class InquiryCrud:

    @staticmethod
    async def create_inquiry(db: AsyncSession, data: InquiryCreate) -> Inquiry:
        inquiry = Inquiry(**data.model_dump())
        db.add(inquiry)
        await db.flush()
        return inquiry

    @staticmethod
    async def get_inquiry(db: AsyncSession, inquiry_id: int) -> Inquiry | None:
        result = await db.execute(select(Inquiry).where(Inquiry.inquiry_id == inquiry_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all(db: AsyncSession) -> list[Inquiry]:
        result = await db.execute(select(Inquiry).order_by(Inquiry.created_at.desc()))
        return list(result.scalars().all())

    @staticmethod
    async def get_by_user(db: AsyncSession, user_id: int) -> list[Inquiry]:
        result = await db.execute(
            select(Inquiry).where(Inquiry.user_id == user_id).order_by(Inquiry.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def answer_inquiry(db: AsyncSession, inquiry: Inquiry, answer: str) -> Inquiry:
        inquiry.answer = answer
        inquiry.status = "ANSWERED"
        inquiry.answered_at = datetime.now()
        await db.flush()
        return inquiry

    @staticmethod
    async def delete_inquiry(db: AsyncSession, inquiry: Inquiry) -> None:
        await db.delete(inquiry)
        await db.flush()
