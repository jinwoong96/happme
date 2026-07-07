import httpx
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import settings
from app.core.jwt_handle import create_access_token, create_refresh_token
from app.db.crud.user import UserCrud
from app.db.scheme.user import UserCreate

KAKAO_AUTH_URL = "https://kauth.kakao.com/oauth/authorize"
KAKAO_TOKEN_URL = "https://kauth.kakao.com/oauth/token"
KAKAO_USERINFO_URL = "https://kapi.kakao.com/v2/user/me"


class KakaoAuthService:

    @staticmethod
    def get_auth_url() -> str:
        params = (
            f"client_id={settings.kakao_client_id}"
            f"&redirect_uri={settings.kakao_redirect_uri}"
            f"&response_type=code"
        )
        return f"{KAKAO_AUTH_URL}?{params}"

    @staticmethod
    async def _get_kakao_user_info(code: str) -> dict:
        async with httpx.AsyncClient() as client:
            token_res = await client.post(KAKAO_TOKEN_URL, data={
                "grant_type": "authorization_code",
                "client_id": settings.kakao_client_id,
                "client_secret": settings.kakao_client_secret,
                "redirect_uri": settings.kakao_redirect_uri,
                "code": code,
            }, headers={"Content-Type": "application/x-www-form-urlencoded"})

            print(f"[KAKAO TOKEN] status={token_res.status_code} body={token_res.text}")

            if token_res.status_code != 200:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="카카오 토큰 교환에 실패했습니다.")

            access_token = token_res.json().get("access_token")

            userinfo_res = await client.get(
                KAKAO_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if userinfo_res.status_code != 200:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="카카오 유저 정보 조회에 실패했습니다.")

            return userinfo_res.json()

    @staticmethod
    async def kakao_login_svc(db: AsyncSession, code: str):
        user_info = await KakaoAuthService._get_kakao_user_info(code)

        kakao_account = user_info.get("kakao_account", {})
        profile = kakao_account.get("profile", {})

        email = kakao_account.get("email")
        name = profile.get("nickname")

        # 이메일 없으면 카카오 ID로 임시 이메일 생성
        if not email:
            kakao_id = user_info.get("id")
            email = f"kakao_{kakao_id}@kakao.com"

        user = await UserCrud.get_by_email(db, email)
        if not user:
            try:
                data = UserCreate(name=name, email=email, password="")
                user = await UserCrud.create_user(db, data)
                await db.commit()
                await db.refresh(user)
            except Exception:
                await db.rollback()
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="카카오 소셜 회원가입에 실패했습니다.")
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