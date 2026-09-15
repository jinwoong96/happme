from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.db.crud.notice import NoticeCrud
from app.db.scheme.notice import NoticeCreate, NoticeUpdate
from app.db.models.notice import Notice


class NoticeService:
    """공지사항 생성/조회/수정/삭제."""

    @staticmethod
    async def create_notice_svc(db: AsyncSession, data: NoticeCreate) -> Notice:
        try:
            notice = await NoticeCrud.create_notice(db, data)
            await db.commit()
            await db.refresh(notice)
            return notice
        except Exception:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="공지사항 생성에 실패했습니다.")

    @staticmethod
    async def get_notice_svc(db: AsyncSession, notice_id: int) -> Notice:
        notice = await NoticeCrud.get_notice(db, notice_id)
        if not notice:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="공지사항을 찾을 수 없습니다.")
        return notice

    @staticmethod
    async def get_all_notices_svc(db: AsyncSession) -> list[Notice]:
        return await NoticeCrud.get_all(db)

    @staticmethod
    async def update_notice_svc(db: AsyncSession, notice_id: int, data: NoticeUpdate) -> Notice:
        notice = await NoticeCrud.get_notice(db, notice_id)
        if not notice:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="공지사항을 찾을 수 없습니다.")
        try:
            updated = await NoticeCrud.update_notice(db, notice, data)
            await db.commit()
            await db.refresh(updated)
            return updated
        except Exception:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="공지사항 수정에 실패했습니다.")

    @staticmethod
    async def delete_notice_svc(db: AsyncSession, notice_id: int) -> dict:
        notice = await NoticeCrud.get_notice(db, notice_id)
        if not notice:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="공지사항을 찾을 수 없습니다.")
        try:
            await NoticeCrud.delete_notice(db, notice)
            await db.commit()
            return {"message": f"notice_id '{notice_id}' 삭제 완료"}
        except Exception:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="공지사항 삭제에 실패했습니다.")
