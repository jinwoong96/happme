from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.db.scheme.user_profile import UserProfileCreate, UserProfileUpdate, UserProfileRead
from app.db.models.user import User
from app.services.user_profile import UserProfileService as profile_svc
from app.core.jwt_handle import get_current_user

router = APIRouter(prefix="/profiles", tags=["UserProfile"])


# C 생성
@router.post("/", response_model=UserProfileRead, status_code=201)
async def create_profile(data: UserProfileCreate, db: AsyncSession = Depends(get_db)):
    return await profile_svc.create_profile_svc(db, data)


# R 조회 - 내 프로필
@router.get("/me", response_model=UserProfileRead)
async def get_my_profile(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await profile_svc.get_profile_svc(db, current_user.user_id)


# R 조회 - user_id로
@router.get("/{user_id}", response_model=UserProfileRead)
async def get_profile(user_id: int, db: AsyncSession = Depends(get_db)):
    return await profile_svc.get_profile_svc(db, user_id)


# U 수정 - 내 프로필
@router.patch("/me", response_model=UserProfileRead)
async def update_my_profile(data: UserProfileUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await profile_svc.update_profile_svc(db, current_user.user_id, data)


# U 수정 - user_id로
@router.patch("/{user_id}", response_model=UserProfileRead)
async def update_profile(user_id: int, data: UserProfileUpdate, db: AsyncSession = Depends(get_db)):
    return await profile_svc.update_profile_svc(db, user_id, data)


# D 삭제
@router.delete("/{user_id}")
async def delete_profile(user_id: int, db: AsyncSession = Depends(get_db)):
    return await profile_svc.delete_profile_svc(db, user_id)
