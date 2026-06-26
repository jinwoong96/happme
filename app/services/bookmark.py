from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.db.crud.bookmark import BookmarkCrud
from app.db.crud.user import UserCrud
from app.db.crud.policy import PolicyCrud
from app.db.scheme.bookmark import BookmarkCreate, BookmarkUpdate
from app.db.models.bookmark import Bookmark


class BookmarkService:

    @staticmethod
    async def create_bookmark_svc(db: AsyncSession, data: BookmarkCreate) -> Bookmark:
        if not await UserCrud.get_user(db, data.user_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="유저를 찾을 수 없습니다.")
        if not await PolicyCrud.get_policy(db, data.policy_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="정책을 찾을 수 없습니다.")
        if await BookmarkCrud.get_by_user_policy(db, data.user_id, data.policy_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="이미 즐겨찾기한 정책입니다.")
        try:
            bookmark = await BookmarkCrud.create_bookmark(db, data)
            await db.commit()
            await db.refresh(bookmark)
            return bookmark
        except Exception:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="즐겨찾기 생성에 실패했습니다.")

    @staticmethod
    async def get_bookmarks_by_user_svc(db: AsyncSession, user_id: int) -> list[Bookmark]:
        if not await UserCrud.get_user(db, user_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="유저를 찾을 수 없습니다.")
        return await BookmarkCrud.get_by_user(db, user_id)

    @staticmethod
    async def update_bookmark_svc(db: AsyncSession, bookmark_id: int, data: BookmarkUpdate) -> Bookmark:
        bookmark = await BookmarkCrud.get_bookmark(db, bookmark_id)
        if not bookmark:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="즐겨찾기를 찾을 수 없습니다.")
        try:
            updated = await BookmarkCrud.update_bookmark(db, bookmark, data)
            await db.commit()
            await db.refresh(updated)
            return updated
        except Exception:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="즐겨찾기 수정에 실패했습니다.")

    @staticmethod
    async def delete_bookmark_svc(db: AsyncSession, bookmark_id: int) -> dict:
        bookmark = await BookmarkCrud.get_bookmark(db, bookmark_id)
        if not bookmark:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="즐겨찾기를 찾을 수 없습니다.")
        try:
            await BookmarkCrud.delete_bookmark(db, bookmark)
            await db.commit()
            return {"message": f"bookmark_id '{bookmark_id}' 삭제 완료"}
        except Exception:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="즐겨찾기 삭제에 실패했습니다.")
