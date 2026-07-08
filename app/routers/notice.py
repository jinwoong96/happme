from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.db.scheme.notice import NoticeCreate, NoticeUpdate, NoticeRead
from app.db.models.user import User
from app.services.notice import NoticeService as notice_svc
from app.core.admin import get_current_admin

router = APIRouter(prefix="/notices", tags=["Notice"])


# C 생성 (관리자용)
@router.post("/", response_model=NoticeRead, status_code=201)
async def create_notice(data: NoticeCreate, db: AsyncSession = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    return await notice_svc.create_notice_svc(db, data)


# R 전체 조회
@router.get("/", response_model=list[NoticeRead])
async def get_all_notices(db: AsyncSession = Depends(get_db)):
    return await notice_svc.get_all_notices_svc(db)


# R 단일 조회
@router.get("/{notice_id}", response_model=NoticeRead)
async def get_notice(notice_id: int, db: AsyncSession = Depends(get_db)):
    return await notice_svc.get_notice_svc(db, notice_id)


# U 수정 (관리자용)
@router.patch("/{notice_id}", response_model=NoticeRead)
async def update_notice(notice_id: int, data: NoticeUpdate, db: AsyncSession = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    return await notice_svc.update_notice_svc(db, notice_id, data)


# D 삭제 (관리자용)
@router.delete("/{notice_id}")
async def delete_notice(notice_id: int, db: AsyncSession = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    return await notice_svc.delete_notice_svc(db, notice_id)
