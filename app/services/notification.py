from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.db.crud.notification import NotificationCrud
from app.db.crud.user import UserCrud
from app.db.crud.notice import NoticeCrud
from app.db.scheme.notification import NotificationCreate, NotificationBroadcastCreate
from app.db.scheme.notice import NoticeCreate
from app.db.models.notification import Notification
from app.db.models.notice import Notice


class NotificationService:

    @staticmethod
    async def create_notification_svc(db: AsyncSession, data: NotificationCreate) -> Notification:
        if not await UserCrud.get_user(db, data.user_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="유저를 찾을 수 없습니다.")
        try:
            notif = await NotificationCrud.create_notification(db, data)
            await db.commit()
            await db.refresh(notif)
            return notif
        except Exception:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="알림 생성에 실패했습니다.")

    @staticmethod
    async def broadcast_svc(db: AsyncSession, admin_id: int, data: NotificationBroadcastCreate) -> Notice:
        try:
            notice = await NoticeCrud.create_notice(db, NoticeCreate(
                admin_id=admin_id, title=data.title, content=data.content, is_pinned=data.is_pinned,
            ))
            users = await UserCrud.get_all(db)
            for user in users:
                await NotificationCrud.create_notification(db, NotificationCreate(
                    user_id=user.user_id, notify_type="NOTICE", title=data.title, content=data.content,
                ))
            await db.commit()
            await db.refresh(notice)
            return notice
        except Exception:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="공지 발송에 실패했습니다.")

    @staticmethod
    async def get_notifications_svc(db: AsyncSession, user_id: int, unread_only: bool = False) -> list[Notification]:
        if not await UserCrud.get_user(db, user_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="유저를 찾을 수 없습니다.")
        return await NotificationCrud.get_by_user(db, user_id, unread_only=unread_only)

    @staticmethod
    async def mark_read_svc(db: AsyncSession, notification_id: int, user_id: int) -> Notification:
        notif = await NotificationCrud.get_notification(db, notification_id)
        if not notif:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="알림을 찾을 수 없습니다.")
        if notif.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="권한이 없습니다.")
        notif = await NotificationCrud.mark_read(db, notif)
        await db.commit()
        await db.refresh(notif)
        return notif

    @staticmethod
    async def mark_all_read_svc(db: AsyncSession, user_id: int) -> dict:
        await NotificationCrud.mark_all_read(db, user_id)
        await db.commit()
        return {"message": "모든 알림을 읽음 처리했습니다."}

    @staticmethod
    async def delete_notification_svc(db: AsyncSession, notification_id: int, user_id: int) -> dict:
        notif = await NotificationCrud.get_notification(db, notification_id)
        if not notif:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="알림을 찾을 수 없습니다.")
        if notif.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="권한이 없습니다.")
        await NotificationCrud.delete_notification(db, notif)
        await db.commit()
        return {"message": f"notification_id '{notification_id}' 삭제 완료"}
