from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.code_master import CodeMaster


class CodeMasterCrud:
    """코드값-이름 매핑 테이블(code_master) 조회. 예: 취업상태 코드 -> "재직자" 같은 표시명."""

    @staticmethod
    async def get_by_group(db: AsyncSession, code_group: str) -> list[CodeMaster]:
        result = await db.execute(
            select(CodeMaster)
            .where(CodeMaster.code_group == code_group)
            .order_by(CodeMaster.sort_order)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_all(db: AsyncSession) -> list[CodeMaster]:
        result = await db.execute(select(CodeMaster).order_by(CodeMaster.code_group, CodeMaster.sort_order))
        return list(result.scalars().all())
