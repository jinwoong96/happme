import httpx
import secrets
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import settings
from app.core.jwt_handle import create_access_token, create_refresh_token
from app.db.crud.user import UserCrud
from app.db.scheme.user import UserCreate

NAVER_AUTH_URL = "https://nid.naver.com/oauth2.0/authorize"
NAVER_TOKEN_URL = "https://nid.naver.com/oauth2.0/token"
NAVER_USERINFO_URL = "https://openapi.naver.com/v1/nid/me"


class NaverAuthService:

    @staticmethod
    def get_auth_url() -> str:
        state = secrets.token_urlsafe(16)
        params = (
            f"client_id={settings.naver_client_id}"
            f"&redirect_uri={settings.naver_redirect_uri}"
            f"&response_type=code"
            f"&state={state}"
        )
        return f"{NAVER_AUTH_URL}?{params}"

    @staticmethod
    async def _get_naver_user_info(code: str, state: str) -> dict:
        async with httpx.AsyncClient() as client:
            # 코드 → 토큰 교환
            token_res = await client.post(NAVER_TOKEN_URL, params={
                "grant_type": "authorization_code",
                "client_id": settings.naver_client_id,
                "client_secret": settings.naver_client_secret,
                "redirect_uri": settings.naver_redirect_uri,
                "code": code,
                "state": state,
            })

            if token_res.status_code != 200:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="네이버 토큰 교환에 실패했습니다.")

            access_token = token_res.json().get("access_token")

            # 토큰 → 유저 정보 조회
            userinfo_res = await client.get(
                NAVER_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if userinfo_res.status_code != 200:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="네이버 유저 정보 조회에 실패했습니다.")

            return userinfo_res.json()

    @staticmethod
    async def naver_login_svc(db: AsyncSession, code: str, state: str):
        user_info = await NaverAuthService._get_naver_user_info(code, state)

        response = user_info.get("response", {})
        email = response.get("email")
        name = response.get("name")

        if not email:
            naver_id = response.get("id")
            email = f"naver_{naver_id}@naver.com"

        user = await UserCrud.get_by_email_and_provider(db, email, "naver")
        if not user:
            try:
                data = UserCreate(name=name, email=email, password="", provider="naver")
                user = await UserCrud.create_user(db, data)
                await db.commit()
                await db.refresh(user)
            except Exception:
                await db.rollback()
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="네이버 소셜 회원가입에 실패했습니다.")
        else:
            if name and user.name != name:
                user.name = name
                await db.commit()
                await db.refresh(user)

        access_token = create_access_token(user.user_id)
        refresh_token = create_refresh_token(user.user_id)
        await UserCrud.update_refresh_token(db, user.user_id, refresh_token)
        await db.commit()
        await db.refresh(user)

        return user, access_token, refresh_token