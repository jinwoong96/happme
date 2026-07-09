from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.db.models.policy import Policy
from app.db.models.policy_region import PolicyRegion
from app.db.scheme.policy import PolicyCreate, PolicyUpdate
from typing import Optional


class PolicyCrud:

    @staticmethod
    async def create_policy(db: AsyncSession, data: PolicyCreate) -> Policy:
        policy = Policy(**data.model_dump())
        db.add(policy)
        await db.flush()
        return policy

    @staticmethod
    async def get_policy(db: AsyncSession, policy_id: int) -> Policy | None:
        result = await db.execute(
            select(Policy).options(selectinload(Policy.regions)).where(Policy.policy_id == policy_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all_policies(
        db: AsyncSession,
        age: Optional[int] = None,
        region: Optional[str] = None,
        lclsf: Optional[str] = None,
        keyword: Optional[str] = None,
        sort: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Policy]:
        stmt = select(Policy).options(selectinload(Policy.regions))
        if age is not None:
            stmt = stmt.where(Policy.sprtTrgtMinAge <= age, Policy.sprtTrgtMaxAge >= age)
        if lclsf:
            stmt = stmt.where(Policy.lclsfNm == lclsf)
        if keyword:
            stmt = stmt.where(
                Policy.plcyNm.ilike(f"%{keyword}%") | Policy.plcyKywdNm.ilike(f"%{keyword}%")
            )
        if region:
            stmt = stmt.join(PolicyRegion, Policy.policy_id == PolicyRegion.policy_id).where(
                PolicyRegion.zip_code.startswith(region)
            )

        if sort == "latest":
            stmt = stmt.order_by(Policy.createdAt.desc())
        elif sort == "popular":
            stmt = stmt.order_by(Policy.inqCnt.desc())
        elif sort == "alpha":
            stmt = stmt.order_by(Policy.plcyNm.asc())

        # "deadline"(마감임박순)은 aplyYmd가 자유 텍스트("YYYYMMDD ~ YYYYMMDD", "상시" 등)라
        # SQL로 안정적으로 정렬할 수 없어 서비스 레이어에서 파싱 후 정렬한다. 정렬 전에 limit을
        # 적용하면 마감일 순으로 앞쪽에 와야 할 항목이 잘려나갈 수 있어 여기서는 limit/offset을
        # 생략하고, 필터링된 전체 결과를 서비스 레이어로 넘긴다.
        if sort != "deadline":
            stmt = stmt.offset(offset).limit(limit)

        result = await db.execute(stmt)
        return list(result.scalars().unique().all())

    @staticmethod
    async def get_policy_ids_by_plcyno(db: AsyncSession, plcy_nos: list[str]) -> dict[str, int]:
        if not plcy_nos:
            return {}
        result = await db.execute(
            select(Policy.plcyNo, Policy.policy_id).where(Policy.plcyNo.in_(plcy_nos))
        )
        return {row.plcyNo: row.policy_id for row in result.all()}

    @staticmethod
    async def update_policy(db: AsyncSession, policy: Policy, data: PolicyUpdate) -> Policy:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(policy, key, value)
        await db.flush()
        return policy

    @staticmethod
    async def increment_inq_cnt(db: AsyncSession, policy: Policy) -> Policy:
        policy.inqCnt += 1
        await db.flush()
        return policy

    @staticmethod
    async def delete_policy(db: AsyncSession, policy: Policy) -> None:
        await db.delete(policy)
        await db.flush()

    @staticmethod
    async def add_region(db: AsyncSession, policy_id: int, zip_code: str) -> PolicyRegion:
        region = PolicyRegion(policy_id=policy_id, zip_code=zip_code)
        db.add(region)
        await db.flush()
        return region

    @staticmethod
    async def delete_region(db: AsyncSession, region: PolicyRegion) -> None:
        await db.delete(region)
        await db.flush()
