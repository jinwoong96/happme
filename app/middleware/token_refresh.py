from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from jwt import ExpiredSignatureError, InvalidTokenError

from app.core.jwt_handle import verify_token, create_access_token, create_refresh_token
from app.core.auth import set_auth_cookies
from app.db.crud.user import UserCrud
from app.db.database import get_db


class RefreshTokenMiddleware(BaseHTTPMiddleware):
    @staticmethod
    def _replace_request_cookie(request: Request, name: str, value: str) -> None:
        cookies = dict(request.cookies)
        cookies[name] = value
        cookie_header = "; ".join(f"{k}={v}" for k, v in cookies.items())

        new_headers = [(k, v) for k, v in request.scope["headers"] if k != b"cookie"]
        new_headers.append((b"cookie", cookie_header.encode("latin-1")))
        request.scope["headers"] = new_headers

    async def dispatch(self, request: Request, call_next):
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