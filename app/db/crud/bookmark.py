from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.bookmark import Bookmark
from app.db.scheme.bookmark import BookmarkCreate, BookmarkUpdate


class BookmarkCrud:

    @staticmethod
    async def create_bookmark(db: AsyncSession, data: BookmarkCreate) -> Bookmark:
        bookmark = Bookmark(**data.model_dump())
        db.add(bookmark)
        await db.flush()
        return bookmark

    @staticmethod
    async def get_bookmark(db: AsyncSession, bookmark_id: int) -> Bookmark | None:
        result = await db.execute(select(Bookmark).where(Bookmark.bookmark_id == bookmark_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_user_policy(db: AsyncSession, user_id: int, policy_id: int) -> Bookmark | None:
        result = await db.execute(
            select(Bookmark).where(Bookmark.user_id == user_id, Bookmark.policy_id == policy_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_user(db: AsyncSession, user_id: int) -> list[Bookmark]:
        result = await db.execute(select(Bookmark).where(Bookmark.user_id == user_id))
        return list(result.scalars().all())

    @staticmethod
    async def update_bookmark(db: AsyncSession, bookmark: Bookmark, data: BookmarkUpdate) -> Bookmark:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(bookmark, key, value)
        await db.flush()
        return bookmark

    @staticmethod
    async def delete_bookmark(db: AsyncSession, bookmark: Bookmark) -> None:
        await db.delete(bookmark)
        await db.flush()
