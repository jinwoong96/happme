from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from app.db.models.local_program import LocalProgram


class LocalProgramCrud:

    @staticmethod
    async def search_by_keyword(db: AsyncSession, keyword: str) -> list[LocalProgram]:
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