import uuid
from datetime import timedelta, datetime, timezone

import jwt
from passlib.context import CryptContext

from app.core.settings import settings
from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db

pwd_crypt = CryptContext(schemes=["bcrypt"])


def get_password_hash(password: str) -> str:
    """비밀번호를 bcrypt로 해시한다."""
    return pwd_crypt.hash(password)


def verify_password(plain_pw: str, hashed_pw: str) -> bool:
    """평문 비밀번호가 저장된 해시와 일치하는지 확인한다."""
    return pwd_crypt.verify(plain_pw, hashed_pw)


def create_token(uid: int, expires_delta: int, **kwargs) -> str:
    """사용자 id와 만료시간(초)으로 JWT를 발급한다. kwargs는 추가로 실어 보낼 클레임(jti 등)."""
    to_encode = kwargs.copy()
    expire = datetime.now(timezone.utc) + timedelta(seconds=expires_delta)
    to_encode.update({"exp": expire, "uid": uid})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(uid: int) -> str:
    """짧은 유효기간의 access token을 발급한다."""
    return create_token(uid=uid, expires_delta=settings.access_token_expire_seconds)


def create_refresh_token(uid: int) -> str:
    """긴 유효기간의 refresh token을 발급한다. jti(고유 id)를 넣어 개별 토큰을 구분할 수 있게 한다."""
    return create_token(uid=uid, expires_delta=settings.refresh_token_expire_seconds, jti=str(uuid.uuid4()))


def decode_token(token: str) -> dict:
    """JWT를 검증하고 payload를 반환한다. 만료/서명 오류 시 jwt 라이브러리 예외를 던진다."""
    return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])


def verify_token(token: str) -> int | None:
    """토큰을 검증해서 안에 담긴 사용자 id(uid)를 꺼낸다."""
    payload = decode_token(token)
    return payload.get("uid")


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)):
    """요청 쿠키의 access_token으로 로그인한 사용자 정보를 DB에서 조회해 반환한다.
    FastAPI Depends로 라우터에 주입해서 쓴다."""
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    try:
        user_id = verify_token(token)
        if not user_id:
            raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="토큰이 만료되었습니다.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")

    from app.db.crud.user import UserCrud
    user = await UserCrud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")
    return user
