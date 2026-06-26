from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.db.scheme.notification import NotificationCreate, NotificationRead
from app.db.models.user import User
from app.services.notification import NotificationService as notif_svc
from app.core.jwt_handle import get_current_user

router = APIRouter(prefix="/notifications", tags=["Notification"])


# C 생성 (시스템/관리자용)
@router.post("/", response_model=NotificationRead, status_code=201)
async def create_notification(data: NotificationCreate, db: AsyncSession = Depends(get_db)):
    return await notif_svc.create_notification_svc(db, data)


# R 내 알림 목록
@router.get("/me", response_model=list[NotificationRead])
async def get_my_notifications(
    unread_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await notif_svc.get_notifications_svc(db, current_user.user_id, unread_only=unread_only)


# U 읽음 처리 - 전체
@router.patch("/me/read-all")
async def mark_all_read(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await notif_svc.mark_all_read_svc(db, current_user.user_id)


# U 읽음 처리 - 단일
@router.patch("/{notification_id}/read", response_model=NotificationRead)
async def mark_read(notification_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await notif_svc.mark_read_svc(db, notification_id, current_user.user_id)


# D 삭제
@router.delete("/{notification_id}")
async def delete_notification(notification_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await notif_svc.delete_notification_svc(db, notification_id, current_user.user_id)
