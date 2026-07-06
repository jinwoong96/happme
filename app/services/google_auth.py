import httpx
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import settings
from app.core.jwt_handle import create_access_token, create_refresh_token
from app.db.crud.user import UserCrud
from app.db.scheme.user import UserCreate

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"


class GoogleAuthService:

    @staticmethod
    def get_auth_url() -> str:
        params = (
            f"client_id={settings.google_client_id}"
            f"&redirect_uri={settings.google_redirect_uri}"
            f"&response_type=code"
            f"&scope=openid%20email%20profile"
            f"&access_type=offline"
        )
        return f"{GOOGLE_AUTH_URL}?{params}"

    @staticmethod
    async def _get_google_user_info(code: str) -> dict:
        async with httpx.AsyncClient() as client:
            token_res = await client.post(GOOGLE_TOKEN_URL, data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.google_redirect_uri,
                "grant_type": "authorization_code",
            })
            if token_res.status_code != 200:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Google 토큰 교환에 실패했습니다.")

            access_token = token_res.json().get("access_token")

            userinfo_res = await client.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if userinfo_res.status_code != 200:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Google 유저 정보 조회에 실패했습니다.")

            return userinfo_res.json()

    @staticmethod
    async def google_login_svc(db: AsyncSession, code: str):
        user_info = await GoogleAuthService._get_google_user_info(code)

        email = user_info.get("email")
        name = user_info.get("name")

        if not email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Google 계정에서 이메일을 가져올 수 없습니다.")

        user = await UserCrud.get_by_email(db, email)
        if not user:
            try:
                data = UserCreate(name=name, email=email, password="")
                user = await UserCrud.create_user(db, data)
                await db.commit()
                await db.refresh(user)
            except Exception:
                await db.rollback()
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="소셜 회원가입에 실패했습니다.")
        else:
            # 기존 유저면 Google 이름으로 업데이트
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