from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from app.db.models.local_program import LocalProgram


class LocalProgramCrud:
    """지역 복지 프로그램(local_program) 테이블 조회."""

    @staticmethod
    async def search_by_keyword(db: AsyncSession, keyword: str) -> list[LocalProgram]:
        """키워드로 지역 프로그램을 검색한다(서비스명/장소명/분류명/지역명 중 하나라도
        일치하면 매치). 위치 정보(위경도)가 있는 프로그램만 대상으로 한다."""
        pattern = f"%{keyword}%"
        stmt = select(LocalProgram).where(
            LocalProgram.latitude.is_not(None),
            LocalProgram.longitude.is_not(None),
            or_(
                LocalProgram.svcnm.ilike(pattern),
                LocalProgram.placenm.ilike(pattern),
                LocalProgram.minclassnm.ilike(pattern),
                LocalProgram.maxclassnm.ilike(pattern),
                LocalProgram.areanm.ilike(pattern),
            ),
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_by_id(db: AsyncSession, local_program_id: int) -> LocalProgram | None:
        result = await db.execute(
            select(LocalProgram).where(LocalProgram.local_program_id == local_program_id)
        )
        return result.scalar_one_or_none()