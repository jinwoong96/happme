from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.notice import Notice
from app.db.scheme.notice import NoticeCreate, NoticeUpdate


class NoticeCrud:
    """공지사항(notice) 테이블에 대한 생성/조회/수정/삭제."""

    @staticmethod
    async def create_notice(db: AsyncSession, data: NoticeCreate) -> Notice:
        notice = Notice(**data.model_dump())
        db.add(notice)
        await db.flush()
        return notice

    @staticmethod
    async def get_notice(db: AsyncSession, notice_id: int) -> Notice | None:
        result = await db.execute(select(Notice).where(Notice.notice_id == notice_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all(db: AsyncSession) -> list[Notice]:
        result = await db.execute(
            select(Notice).order_by(Notice.is_pinned.desc(), Notice.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def update_notice(db: AsyncSession, notice: Notice, data: NoticeUpdate) -> Notice:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(notice, key, value)
        await db.flush()
        return notice

    @staticmethod
    async def delete_notice(db: AsyncSession, notice: Notice) -> None:
        await db.delete(notice)
        await db.flush()
