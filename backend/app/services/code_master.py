from sqlalchemy.ext.asyncio import AsyncSession
from app.db.crud.code_master import CodeMasterCrud
from app.db.models.code_master import CodeMaster


class CodeMasterService:
    """코드값-표시명 매핑 조회(회원가입/프로필 폼의 드롭다운 항목 등에 사용)."""

    @staticmethod
    async def get_by_group_svc(db: AsyncSession, code_group: str) -> list[CodeMaster]:
        return await CodeMasterCrud.get_by_group(db, code_group)

    @staticmethod
    async def get_all_svc(db: AsyncSession) -> list[CodeMaster]:
        return await CodeMasterCrud.get_all(db)
