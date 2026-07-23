from fastapi import Depends, HTTPException, status
from app.db.models.user import User
from app.core.jwt_handle import get_current_user


async def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """현재 로그인한 사용자가 관리자(ADMIN)인지 확인한다. 아니면 403 에러를 던진다."""
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="관리자 권한이 필요합니다.")
    return current_user
