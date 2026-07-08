from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.db.scheme.user import UserCreate, UserUpdate, UserRead, UserLogin, UserPasswordUpdate
from app.db.models.user import User
from app.services.user import UserService as user_svc
from app.core.jwt_handle import get_current_user
from app.core.admin import get_current_admin

router = APIRouter(prefix="/users", tags=["User"])


# C 회원가입
@router.post("/", response_model=UserRead, status_code=201)
async def create_user(data: UserCreate, db: AsyncSession = Depends(get_db)):
    return await user_svc.create_user_svc(db, data)


# 로그인
@router.post("/login")
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    user, access_token, refresh_token = await user_svc.login_svc(db, data)
    response = JSONResponse(content={"user": UserRead.model_validate(user).model_dump(mode="json")})
    response.set_cookie(key="access_token", value=access_token, httponly=True, samesite="none", secure=True)
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, samesite="none", secure=True)
    return response


# 로그아웃
@router.post("/logout")
async def logout(response: Response, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    await user_svc.logout_svc(db, current_user.user_id)
    response.delete_cookie(key="access_token", httponly=True, samesite="none", secure=True)
    response.delete_cookie(key="refresh_token", httponly=True, samesite="none", secure=True)
    return {"message": "로그아웃 성공"}


# R 내 정보 조회
@router.get("/me", response_model=UserRead)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserRead.model_validate(current_user)


# R 전체 조회 (관리자용)
@router.get("/", response_model=list[UserRead])
async def get_all_users(db: AsyncSession = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    return await user_svc.get_all_users_svc(db)


# R 단일 조회
@router.get("/{user_id}", response_model=UserRead)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    return await user_svc.get_user_svc(db, user_id)


# U 내 정보 수정
@router.patch("/me", response_model=UserRead)
async def update_me(data: UserUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await user_svc.update_user_svc(db, current_user.user_id, data)


# U 비밀번호 변경
@router.patch("/me/password")
async def update_password(data: UserPasswordUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await user_svc.update_password_svc(db, current_user, data)


# D 회원 탈퇴 (본인)
@router.delete("/me")
async def delete_me(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await user_svc.delete_user_svc(db, current_user.user_id)


# D 삭제 (관리자용)
@router.delete("/{user_id}")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    if user_id == current_admin.user_id:
        raise HTTPException(status_code=400, detail="본인 계정은 삭제할 수 없습니다.")
    return await user_svc.delete_user_svc(db, user_id)
