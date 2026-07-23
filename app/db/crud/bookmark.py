from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.db.models.bookmark import Bookmark
from app.db.models.policy import Policy
from app.db.scheme.bookmark import BookmarkCreate, BookmarkUpdate


class BookmarkCrud:
    """즐겨찾기(bookmark) 테이블에 대한 생성/조회/수정/삭제. 정책 즐겨찾기와
    지역 프로그램 즐겨찾기를 하나의 테이블로 같이 다룬다."""

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
    async def get_by_user_with_policy(db: AsyncSession, user_id: int) -> list[Bookmark]:
        result = await db.execute(
            select(Bookmark)
            .options(
                selectinload(Bookmark.policy).selectinload(Policy.schedule_events),
                selectinload(Bookmark.policy).selectinload(Policy.ai_tip),
            )
            .where(Bookmark.user_id == user_id)
        )
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

    @staticmethod
    async def get_by_user_local_program(db: AsyncSession, user_id: int, local_program_id: int) -> Bookmark | None:
        result = await db.execute(
            select(Bookmark).where(Bookmark.user_id == user_id, Bookmark.local_program_id == local_program_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_alarm_targets_by_deadline(db: AsyncSession, target_date: date) -> list[Bookmark]:
        """알림(alarm_yn=True) 켜둔 즐겨찾기 중, 정책 마감일(aplyEndDt)이 target_date인 것만 policy와 함께 조회.
        마감 하루 전 알림 배치에서 사용."""
        result = await db.execute(
            select(Bookmark)
            .join(Policy, Bookmark.policy_id == Policy.policy_id)
            .options(selectinload(Bookmark.policy))
            .where(Bookmark.alarm_yn == True, Policy.aplyEndDt == target_date)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_by_user_with_targets(db: AsyncSession, user_id: int) -> list[Bookmark]:
        """정책+지역 프로그램 즐겨찾기를 한 번에 eager load."""
        result = await db.execute(
            select(Bookmark)
            .options(
                selectinload(Bookmark.policy).selectinload(Policy.schedule_events),
                selectinload(Bookmark.policy).selectinload(Policy.ai_tip),
                selectinload(Bookmark.local_program),
            )
            .where(Bookmark.user_id == user_id)
        )
        return list(result.scalars().all())