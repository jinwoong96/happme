import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.core.settings import settings
from app.db.crud.bookmark import BookmarkCrud
from app.db.crud.user import UserCrud
from app.db.crud.policy import PolicyCrud
from app.db.crud.policy_schedule_event import PolicyScheduleEventCrud
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
    async def _ensure_schedule(db: AsyncSession, policy: Policy) -> tuple[list[dict], str | None]:
        """정책의 일정/팁이 DB에 없으면 bene_ai를 호출해서 추출하고 저장한다.
        bene_ai가 꺼져있거나 실패해도 예외를 삼키고 빈 결과로 degrade 한다.
        반환값은 항상 {event_type, event_date, raw_text} 형태의 dict 리스트로 정규화한다."""
        if policy.schedule_events or policy.ai_tip:
            events_read = [
                {"event_type": e.event_type, "event_date": e.event_date, "raw_text": e.raw_text}
                for e in policy.schedule_events
            ]
            return events_read, (policy.ai_tip.tip if policy.ai_tip else None)

        payload = {
            "plcyNm": policy.plcyNm,
            "plcyExplnCn": policy.plcyExplnCn or "",
            "plcyAplyMthdCn": policy.plcyAplyMthdCn or "",
            "srngMthdCn": policy.srngMthdCn or "",
            "aplyYmd": policy.aplyYmd or "",
            "frstRegDt": policy.frstRegDt.isoformat() if policy.frstRegDt else "",
        }
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(f"{settings.ai_service_url}/schedule/extract", json=payload)
                resp.raise_for_status()
                data = resp.json()
        except Exception:
            return [], None

        raw_events = data.get("events") or []
        prep_tip = data.get("prep_tip")
        events_read = [
            {"event_type": e["type"], "event_date": e["date"], "raw_text": e["raw_text"]}
            for e in raw_events
        ]

        try:
            if raw_events:
                await PolicyScheduleEventCrud.bulk_create(db, policy.policy_id, raw_events)
            if prep_tip:
                await PolicyScheduleEventCrud.create_tip(db, policy.policy_id, prep_tip)
            await db.commit()
        except Exception:
            await db.rollback()

        return events_read, prep_tip

    @staticmethod
    async def get_calendar_svc(db: AsyncSession, user_id: int) -> list[BookmarkCalendarItem]:
        bookmarks = await BookmarkCrud.get_by_user_with_policy(db, user_id)

        items = []
        for bookmark in bookmarks:
            policy = bookmark.policy
            events, prep_tip = await BookmarkService._ensure_schedule(db, policy)
            items.append(BookmarkCalendarItem(
                bookmark_id=bookmark.bookmark_id,
                policy_id=policy.policy_id,
                plcyNm=policy.plcyNm,
                sprvsnInstCdNm=policy.sprvsnInstCdNm,
                aplyYmd=policy.aplyYmd,
                events=events,
                prep_tip=prep_tip,
            ))
        return items
