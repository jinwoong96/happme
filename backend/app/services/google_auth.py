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
    """구글 소셜 로그인. OAuth 인가 URL 생성, 콜백에서 받은 code로 사용자 정보를 받아
    최초 로그인이면 회원가입까지 처리한다."""

    @staticmethod
    def get_auth_url() -> str:
        """구글 로그인 동의 화면으로 보낼 URL을 만든다."""
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
        """콜백으로 받은 인가 코드를 구글 access token으로 교환하고, 그 토큰으로 사용자
        정보(이메일/이름)를 조회한다."""
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
        """구글 계정으로 로그인한다. 처음 로그인이면 계정을 새로 만들고, 이름이 바뀌었으면
        갱신한 뒤, 우리 서비스용 access/refresh 토큰을 발급한다."""
        user_info = await GoogleAuthService._get_google_user_info(code)

        email = user_info.get("email")
        name = user_info.get("name")

        if not email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Google 계정에서 이메일을 가져올 수 없습니다.")

        user = await UserCrud.get_by_email_and_provider(db, email, "google")
        if not user:
            try:
                data = UserCreate(name=name, email=email, password="", provider="google")
                user = await UserCrud.create_user(db, data)
                await db.commit()
                await db.refresh(user)
            except Exception:
                await db.rollback()
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="소셜 회원가입에 실패했습니다.")
        else:
            # 기존 구글 계정이면 Google 이름으로 업데이트
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