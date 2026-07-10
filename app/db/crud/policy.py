from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, case, or_
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
        include_closed: bool = False,
        consonant: Optional[str] = None,
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
        if not include_closed:
            # 마감일을 모르는 정책(NULL, 상시 등)은 마감됐다고 판단할 근거가 없으므로 계속 보여준다.
            stmt = stmt.where(or_(Policy.aplyEndDt.is_(None), Policy.aplyEndDt >= date.today()))

        if sort == "latest":
            stmt = stmt.order_by(Policy.createdAt.desc())
        elif sort == "popular":
            stmt = stmt.order_by(Policy.inqCnt.desc())
        elif sort == "alpha":
            stmt = stmt.order_by(Policy.plcyNm.asc())
        elif sort == "deadline":
            today = date.today()
            # 아직 마감 전(아래로 갈수록 우선순위 낮음): 1) 마감일 없음(NULL, 상시 등)은 맨 뒤,
            # 2) 이미 마감 지난 건 그 다음(최근에 마감된 것부터), 3) 아직 유효한 건 마감일이
            # 가까운 순으로 맨 앞.
            stmt = stmt.order_by(
                case((Policy.aplyEndDt.is_(None), 1), else_=0).asc(),
                case((Policy.aplyEndDt < today, 1), else_=0).asc(),
                case((Policy.aplyEndDt >= today, Policy.aplyEndDt), else_=None).asc(),
                case((Policy.aplyEndDt < today, Policy.aplyEndDt), else_=None).desc(),
            )

        # 초성 필터는 첫 글자 초성을 계산해야 해서 SQL로는 안정적으로 걸러낼 수 없어 서비스
        # 레이어에서 파이썬으로 필터링한다. limit을 여기서 적용하면 필터링 전에 잘려나가
        # 결과가 부족해질 수 있어, 초성 필터가 있을 때는 limit/offset을 생략한다.
        if not consonant:
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
    async def increment_bookmark_cnt(db: AsyncSession, policy: Policy) -> Policy:
        policy.bookmarkCnt += 1
        await db.flush()
        return policy

    @staticmethod
    async def decrement_bookmark_cnt(db: AsyncSession, policy: Policy) -> Policy:
        policy.bookmarkCnt = max(policy.bookmarkCnt - 1, 0)
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
