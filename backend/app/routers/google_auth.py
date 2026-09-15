from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.scheme.user import UserRead
from app.core.settings import settings
from app.services.google_auth import GoogleAuthService as google_svc

router = APIRouter(prefix="/auth/google", tags=["GoogleAuth"])


# Google 로그인 페이지로 리다이렉트
@router.get("/login")
async def google_login():
    return RedirectResponse(url=google_svc.get_auth_url())


# Google 콜백 — 코드 받아서 로그인 처리
@router.get("/callback")
async def google_callback(code: str, db: AsyncSession = Depends(get_db)):
    user, access_token, refresh_token = await google_svc.google_login_svc(db, code)

    # 로그인 성공 후 프론트 홈으로 리다이렉트
    response = RedirectResponse(url=settings.frontend_url)
    response.set_cookie(key="access_token", value=access_token, httponly=True, samesite="none", secure=True)
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, samesite="none", secure=True)
    return response