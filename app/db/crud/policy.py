from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, case, or_, func
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
        mclsf: Optional[str] = None,
        keyword: Optional[str] = None,
        sort: Optional[str] = None,
        include_closed: bool = False,
        consonant: Optional[str] = None,
        exclude_ids: Optional[list[int]] = None,
        exclude_names: Optional[list[str]] = None,
        max_sprt_amt_not_null: bool = False,
        max_sprt_amt_below: Optional[int] = None,
        deadline_within_days: Optional[int] = None,
        exclude_keywords: Optional[list[str]] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Policy]:
        stmt = select(Policy).options(selectinload(Policy.regions))
        if age is not None:
            stmt = stmt.where(Policy.sprtTrgtMinAge <= age, Policy.sprtTrgtMaxAge >= age)
        if lclsf:
            stmt = stmt.where(Policy.lclsfNm == lclsf)
        if mclsf:
            stmt = stmt.where(Policy.mclsfNm == mclsf)
        if keyword:
            # 정책명 띄어쓰기가 기관마다 제각각이라(예: "전세보증금 반환보증" vs "전세보증금반환보증"),
            # 검색어/컬럼 양쪽 다 공백을 제거하고 부분일치시킨다.
            normalized_keyword = keyword.replace(" ", "").replace("　", "")
            stmt = stmt.where(
                func.replace(Policy.plcyNm, ' ', '').ilike(f"%{normalized_keyword}%")
                | func.replace(Policy.plcyKywdNm, ' ', '').ilike(f"%{normalized_keyword}%")
            )
        if region:
            # JOIN을 쓰면 전국 단위 정책(policy_region 행이 수백 개)이 매칭 행을 여러 개
            # 만들어내서, 뒤에서 offset/limit이 그 중복 행 기준으로 적용되어 실제로는 소수의
            # 정책만 살아남는 문제가 있었다. 서브쿼리로 policy_id만 걸러내면 정책당 한 행만
            # 나오므로 이 문제가 없다.
            matching_policy_ids = select(PolicyRegion.policy_id).where(PolicyRegion.zip_code.startswith(region))
            stmt = stmt.where(Policy.policy_id.in_(matching_policy_ids))
        if not include_closed:
            # 마감일을 모르는 정책(NULL, 상시 등)은 마감됐다고 판단할 근거가 없으므로 계속 보여준다.
            stmt = stmt.where(or_(Policy.aplyEndDt.is_(None), Policy.aplyEndDt >= date.today()))
        if exclude_ids:
            stmt = stmt.where(Policy.policy_id.notin_(exclude_ids))
        if exclude_names:
            # policy_id는 다르지만 plcyNm이 같은 정책(같은 정책이 다른 연도/기관으로 재등록된 경우
            # 등)까지 걸러내기 위한 이름 기준 제외.
            stmt = stmt.where(Policy.plcyNm.notin_(exclude_names))
        if max_sprt_amt_not_null:
            stmt = stmt.where(Policy.maxSprtAmt.isnot(None))
        if max_sprt_amt_below is not None:
            stmt = stmt.where(Policy.maxSprtAmt < max_sprt_amt_below)
        if deadline_within_days is not None:
            threshold = date.today() + timedelta(days=deadline_within_days)
            stmt = stmt.where(Policy.aplyEndDt.isnot(None), Policy.aplyEndDt <= threshold)
        if exclude_keywords:
            # plcyKywdNm이 NULL인 정책은 해당 키워드가 없는 것이므로 계속 보여준다.
            for kw in exclude_keywords:
                stmt = stmt.where(or_(Policy.plcyKywdNm.is_(None), ~Policy.plcyKywdNm.ilike(f"%{kw}%")))

        if sort == "latest":
            stmt = stmt.order_by(Policy.createdAt.desc())
        elif sort == "popular":
            stmt = stmt.order_by(Policy.inqCnt.desc())
        elif sort == "alpha":
            stmt = stmt.order_by(Policy.plcyNm.asc())
        elif sort == "amount":
            stmt = stmt.where(Policy.maxSprtAmt.isnot(None)).order_by(Policy.maxSprtAmt.desc())
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
    async def get_distinct_mclsf(db: AsyncSession) -> list[str]:
        result = await db.execute(
            select(Policy.mclsfNm).where(Policy.mclsfNm.is_not(None)).distinct().order_by(Policy.mclsfNm.asc())
        )
        return [row[0] for row in result.all() if row[0]]

    @staticmethod
    async def get_policies_by_ids(db: AsyncSession, policy_ids: list[int]) -> list[Policy]:
        if not policy_ids:
            return []
        result = await db.execute(
            select(Policy).options(selectinload(Policy.regions)).where(Policy.policy_id.in_(policy_ids))
        )
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
    async def get_summaries_by_plcyno(db: AsyncSession, plcy_nos: list[str]) -> dict[str, str]:
        if not plcy_nos:
            return {}
        result = await db.execute(
            select(Policy.plcyNo, Policy.summary).where(Policy.plcyNo.in_(plcy_nos))
        )
        return {row.plcyNo: row.summary for row in result.all() if row.summary}

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
