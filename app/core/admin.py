from fastapi import Depends, HTTPException, status
from app.db.models.user import User
from app.core.jwt_handle import get_current_user


async def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="관리자 권한이 필요합니다.")
    return current_user
