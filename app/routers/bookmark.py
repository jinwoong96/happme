from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.db.scheme.bookmark import BookmarkCreate, BookmarkUpdate, BookmarkRead
from app.db.models.user import User
from app.services.bookmark import BookmarkService as bookmark_svc
from app.core.jwt_handle import get_current_user

router = APIRouter(prefix="/bookmarks", tags=["Bookmark"])


# C 생성
@router.post("/", response_model=BookmarkRead, status_code=201)
async def create_bookmark(data: BookmarkCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await bookmark_svc.create_bookmark_svc(db, data)


# R 내 즐겨찾기 목록
@router.get("/me", response_model=list[BookmarkRead])
async def get_my_bookmarks(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await bookmark_svc.get_bookmarks_by_user_svc(db, current_user.user_id)


# R 유저별 즐겨찾기 목록
@router.get("/user/{user_id}", response_model=list[BookmarkRead])
async def get_bookmarks_by_user(user_id: int, db: AsyncSession = Depends(get_db)):
    return await bookmark_svc.get_bookmarks_by_user_svc(db, user_id)


# U 알림 설정 수정
@router.patch("/{bookmark_id}", response_model=BookmarkRead)
async def update_bookmark(bookmark_id: int, data: BookmarkUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await bookmark_svc.update_bookmark_svc(db, bookmark_id, data)


# D 삭제
@router.delete("/{bookmark_id}")
async def delete_bookmark(bookmark_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await bookmark_svc.delete_bookmark_svc(db, bookmark_id)
