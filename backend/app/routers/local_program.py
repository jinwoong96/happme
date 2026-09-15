from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.db.scheme.local_program import LocalProgramSearchResponse
from app.services.local_program import LocalProgramService as local_program_svc

router = APIRouter(prefix="/local-programs", tags=["LocalProgram"])


# R 지역 프로그램 검색 (키워드 필수, 위치 정보가 있으면 거리순으로도 정렬)
@router.get("/search", response_model=LocalProgramSearchResponse)
async def search_local_programs(
    keyword: str = Query(..., description="검색어"),
    lat: Optional[float] = Query(None, description="사용자 위도"),
    lng: Optional[float] = Query(None, description="사용자 경도"),
    radius: Optional[float] = Query(None, description="반경(km)"),
    db: AsyncSession = Depends(get_db),
):
    return await local_program_svc.search_svc(db, keyword, lat=lat, lng=lng, radius=radius)
