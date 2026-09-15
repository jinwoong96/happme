from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.policy_income_required import PolicyIncomeRequired


class PolicyIncomeRequiredCrud:
    """정책별 소득 확인 시 물어봐야 할 필드 목록(policy_income_required) 조회."""

    @staticmethod
    async def get_required_fields_by_plcyno(db: AsyncSession, plcy_nos: list[str]) -> dict[str, list[str]]:
        """plcyNo -> required_fields(list[str]) 매핑. 행이 없으면 결과에서 빠지므로(=빈 리스트로 취급) 호출 측에서 기본값 처리."""
        if not plcy_nos:
            return {}
        result = await db.execute(
            select(PolicyIncomeRequired.plcyNo, PolicyIncomeRequired.required_fields)
            .where(PolicyIncomeRequired.plcyNo.in_(plcy_nos))
        )
        return {row.plcyNo: row.required_fields for row in result.all()}
