from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.db.scheme.code_master import CodeMasterRead
from app.services.code_master import CodeMasterService as code_svc

router = APIRouter(prefix="/codes", tags=["CodeMaster"])


# R 그룹별 코드 조회
@router.get("/{code_group}", response_model=list[CodeMasterRead])
async def get_codes_by_group(code_group: str, db: AsyncSession = Depends(get_db)):
    return await code_svc.get_by_group_svc(db, code_group)


# R 전체 코드 조회
@router.get("/", response_model=list[CodeMasterRead])
async def get_all_codes(db: AsyncSession = Depends(get_db)):
    return await code_svc.get_all_svc(db)
