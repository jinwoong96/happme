from sqlalchemy.ext.asyncio import AsyncSession
from app.db.crud.code_master import CodeMasterCrud
from app.db.models.code_master import CodeMaster


class CodeMasterService:

    @staticmethod
    async def get_by_group_svc(db: AsyncSession, code_group: str) -> list[CodeMaster]:
        return await CodeMasterCrud.get_by_group(db, code_group)

    @staticmethod
    async def get_all_svc(db: AsyncSession) -> list[CodeMaster]:
        return await CodeMasterCrud.get_all(db)
