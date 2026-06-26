from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.notification import Notification
from app.db.scheme.notification import NotificationCreate


class NotificationCrud:

    @staticmethod
    async def create_notification(db: AsyncSession, data: NotificationCreate) -> Notification:
        notif = Notification(**data.model_dump())
        db.add(notif)
        await db.flush()
        return notif

    @staticmethod
    async def get_notification(db: AsyncSession, notification_id: int) -> Notification | None:
        result = await db.execute(select(Notification).where(Notification.notification_id == notification_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_user(db: AsyncSession, user_id: int, unread_only: bool = False) -> list[Notification]:
        stmt = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            stmt = stmt.where(Notification.is_read == False)
        stmt = stmt.order_by(Notification.created_at.desc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def mark_read(db: AsyncSession, notification: Notification) -> Notification:
        notification.is_read = True
        await db.flush()
        return notification

    @staticmethod
    async def mark_all_read(db: AsyncSession, user_id: int) -> None:
        result = await db.execute(
            select(Notification).where(Notification.user_id == user_id, Notification.is_read == False)
        )
        for notif in result.scalars().all():
            notif.is_read = True
        await db.flush()

    @staticmethod
    async def delete_notification(db: AsyncSession, notification: Notification) -> None:
        await db.delete(notification)
        await db.flush()
