from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.policy_summary_cache import PolicySummaryCache

class PolicySummaryCacheCrud:

    @staticmethod
    async def get_cache(db: AsyncSession, policy_name: str) -> PolicySummaryCache | None:
        result = await db.execute(
            select(PolicySummaryCache).where(PolicySummaryCache.policy_name == policy_name)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def set_cache(db: AsyncSession, policy_name: str, summary_text: str) -> PolicySummaryCache:
        cache = PolicySummaryCache(policy_name=policy_name, summary_text=summary_text)
        db.add(cache)
        await db.commit()
        await db.refresh(cache)
        return cache