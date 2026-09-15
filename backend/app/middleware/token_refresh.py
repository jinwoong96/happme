from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from jwt import ExpiredSignatureError, InvalidTokenError

from app.core.jwt_handle import verify_token, create_access_token, create_refresh_token
from app.core.auth import set_auth_cookies
from app.db.crud.user import UserCrud
from app.db.database import get_db


class RefreshTokenMiddleware(BaseHTTPMiddleware):
    """access_token이 만료됐지만 refresh_token이 유효하면, 요청을 막지 않고 그 자리에서
    새 토큰 쌍을 발급해 요청에도 반영하고 응답 쿠키로도 내려준다(사용자가 로그인이
    끊긴 걸 느끼지 못하게 하는 자동 갱신)."""

    @staticmethod
    def _replace_request_cookie(request: Request, name: str, value: str) -> None:
        """미들웨어가 새로 발급한 토큰을, 뒤이어 실행될 라우터가 이번 요청 안에서 바로
        쓸 수 있도록 요청 객체의 쿠키 헤더를 새 값으로 바꿔치기한다."""
        cookies = dict(request.cookies)
        cookies[name] = value
        cookie_header = "; ".join(f"{k}={v}" for k, v in cookies.items())

        new_headers = [(k, v) for k, v in request.scope["headers"] if k != b"cookie"]
        new_headers.append((b"cookie", cookie_header.encode("latin-1")))
        request.scope["headers"] = new_headers

    async def dispatch(self, request: Request, call_next):
        """access_token이 유효하지 않고 refresh_token이 유효하면 새 토큰을 발급해서
        DB에 반영하고, 요청/응답 양쪽에 새 토큰을 적용한 뒤 다음 핸들러를 호출한다."""
        access_token = request.cookies.get("access_token")
        refresh_token = request.cookies.get("refresh_token")

        access_valid = False
        if access_token:
            try:
                verify_token(access_token)
                access_valid = True
            except (ExpiredSignatureError, InvalidTokenError):
                access_valid = False

        new_access_token = None
        new_refresh_token = None

        if not access_valid and refresh_token:
            try:
                user_id = verify_token(refresh_token)
            except (ExpiredSignatureError, InvalidTokenError):
                user_id = None

            if user_id:
                new_access_token = create_access_token(user_id)
                new_refresh_token = create_refresh_token(user_id)

                try:
                    db = await anext(get_db())
                    await UserCrud.update_refresh_token(db, user_id, new_refresh_token)
                    await db.commit()
                except Exception:
                    new_access_token = None
                    new_refresh_token = None

            if new_access_token:
                self._replace_request_cookie(request, "access_token", new_access_token)

        response = await call_next(request)

        if new_access_token:
            set_auth_cookies(response, new_access_token, new_refresh_token)

        return response