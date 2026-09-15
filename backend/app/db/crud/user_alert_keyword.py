from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.user_alert_keyword import UserAlertKeyword
from app.db.scheme.user_alert_keyword import UserAlertKeywordCreate


class UserAlertKeywordCrud:
    """사용자가 등록한 알림 키워드(user_alert_keyword) 조회/생성/삭제."""

    @staticmethod
    async def create_keyword(db: AsyncSession, data: UserAlertKeywordCreate) -> UserAlertKeyword:
        keyword = UserAlertKeyword(**data.model_dump())
        db.add(keyword)
        await db.flush()
        return keyword

    @staticmethod
    async def get_keyword(db: AsyncSession, keyword_id: int) -> UserAlertKeyword | None:
        result = await db.execute(select(UserAlertKeyword).where(UserAlertKeyword.keyword_id == keyword_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_user_keyword(db: AsyncSession, user_id: int, keyword: str) -> UserAlertKeyword | None:
        result = await db.execute(
            select(UserAlertKeyword).where(UserAlertKeyword.user_id == user_id, UserAlertKeyword.keyword == keyword)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_user(db: AsyncSession, user_id: int) -> list[UserAlertKeyword]:
        result = await db.execute(
            select(UserAlertKeyword)
            .where(UserAlertKeyword.user_id == user_id)
            .order_by(UserAlertKeyword.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_all_active(db: AsyncSession) -> list[UserAlertKeyword]:
        """정책 신규/변경 감지 배치에서 전체 구독자를 조회할 때 사용."""
        result = await db.execute(select(UserAlertKeyword).where(UserAlertKeyword.is_active == True))
        return list(result.scalars().all())

    @staticmethod
    async def delete_keyword(db: AsyncSession, keyword: UserAlertKeyword) -> None:
        await db.delete(keyword)
        await db.flush()
