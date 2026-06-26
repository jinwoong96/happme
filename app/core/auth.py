from typing import Optional

from fastapi import Request, Response, HTTPException, status
from jwt import ExpiredSignatureError, InvalidSignatureError
from app.core.settings import settings
from app.core.jwt_handle import verify_token


def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=int(settings.access_token_expire_seconds),
        secure=True,
        httponly=True,
        samesite="none",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=int(settings.refresh_token_expire_seconds),
        secure=True,
        httponly=True,
        samesite="none",
    )


async def get_user_id(request: Request) -> int:
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Access token is missing")
    try:
        user_id = verify_token(access_token)
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No such user")
        return user_id
    except ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Access Token expired")
    except InvalidSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Access Token")


async def get_optional(request: Request) -> Optional[int]:
    access_token = request.cookies.get("access_token")
    if not access_token:
        return None
    try:
        return verify_token(access_token)
    except (ExpiredSignatureError, InvalidSignatureError):
        return None
