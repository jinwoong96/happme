from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.services.naver_auth import NaverAuthService as naver_svc
from app.core.settings import settings

router = APIRouter(prefix="/auth/naver", tags=["NaverAuth"])


# 네이버 로그인 페이지로 리다이렉트
@router.get("/login")
async def naver_login():
    return RedirectResponse(url=naver_svc.get_auth_url())


# 네이버 콜백 — 코드 받아서 로그인 처리
@router.get("/callback")
async def naver_callback(code: str, state: str, db: AsyncSession = Depends(get_db)):
    user, access_token, refresh_token = await naver_svc.naver_login_svc(db, code, state)

    response = RedirectResponse(url=settings.frontend_url)
    response.set_cookie(key="access_token", value=access_token, httponly=True, samesite="none", secure=True)
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, samesite="none", secure=True)
    return response