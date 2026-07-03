from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.db.crud.bookmark import BookmarkCrud
from app.db.crud.user import UserCrud
from app.db.crud.policy import PolicyCrud
from app.db.scheme.bookmark import BookmarkCreate, BookmarkUpdate, BookmarkCalendarItem
from app.db.models.bookmark import Bookmark
from app.db.models.policy import Policy


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

    @staticmethod
    async def get_calendar_svc(db: AsyncSession, user_id: int) -> list[BookmarkCalendarItem]:
        """즐겨찾기 캘린더는 미리 적재해둔 policy_schedule_event/policy_ai_tip과
        policy.aplyYmd만 읽는다. LLM을 그 자리에서 호출하지 않으므로 지연이 없다."""
        bookmarks = await BookmarkCrud.get_by_user_with_policy(db, user_id)

        items = []
        for bookmark in bookmarks:
            policy = bookmark.policy
            events = [
                {"event_type": e.event_type, "event_date": e.event_date, "raw_text": e.raw_text}
                for e in policy.schedule_events
            ]
            items.append(BookmarkCalendarItem(
                bookmark_id=bookmark.bookmark_id,
                policy_id=policy.policy_id,
                plcyNm=policy.plcyNm,
                sprvsnInstCdNm=policy.sprvsnInstCdNm,
                aplyYmd=policy.aplyYmd,
                events=events,
                prep_tip=policy.ai_tip.tip if policy.ai_tip else None,
            ))
        return items
