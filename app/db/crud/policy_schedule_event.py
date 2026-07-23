from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.policy_schedule_event import PolicyScheduleEvent
from app.db.models.policy_ai_tip import PolicyAiTip


class PolicyScheduleEventCrud:
    """정책 일정(policy_schedule_event)과 AI 준비 팁(policy_ai_tip) 조회/생성."""

    @staticmethod
    async def get_by_policy(db: AsyncSession, policy_id: int) -> list[PolicyScheduleEvent]:
        result = await db.execute(
            select(PolicyScheduleEvent).where(PolicyScheduleEvent.policy_id == policy_id)
        )
        return list(result.scalars().all())

    @staticmethod
    async def bulk_create(db: AsyncSession, policy_id: int, events: list[dict]) -> list[PolicyScheduleEvent]:
        """bene_ai가 추출한 일정 목록(type/date/raw_text dict)을 한 번에 저장한다."""
        rows = [
            PolicyScheduleEvent(
                policy_id=policy_id,
                event_type=e["type"],
                event_date=e["date"],
                raw_text=e["raw_text"],
            )
            for e in events
        ]
        db.add_all(rows)
        await db.flush()
        return rows

    @staticmethod
    async def get_tip(db: AsyncSession, policy_id: int) -> PolicyAiTip | None:
        result = await db.execute(select(PolicyAiTip).where(PolicyAiTip.policy_id == policy_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def create_tip(db: AsyncSession, policy_id: int, tip: str) -> PolicyAiTip:
        row = PolicyAiTip(policy_id=policy_id, tip=tip)
        db.add(row)
        await db.flush()
        return row
