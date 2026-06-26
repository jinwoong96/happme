from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.db.crud.user import UserCrud
from app.db.scheme.user import UserCreate, UserUpdate, UserLogin, UserPasswordUpdate, UserRead
from app.db.models.user import User
from app.core.jwt_handle import create_access_token, create_refresh_token, get_password_hash, verify_password


class UserService:

    @staticmethod
    async def create_user_svc(db: AsyncSession, data: UserCreate) -> User:
        if await UserCrud.get_by_email(db, data.email):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="이미 사용 중인 이메일입니다.")
        data.password = get_password_hash(data.password)
        try:
            user = await UserCrud.create_user(db, data)
            await db.commit()
            await db.refresh(user)
            return user
        except Exception:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="회원가입에 실패했습니다.")

    @staticmethod
    async def get_user_svc(db: AsyncSession, user_id: int) -> User:
        user = await UserCrud.get_user(db, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"user_id '{user_id}'에 해당하는 유저가 없습니다.")
        return user

    @staticmethod
    async def get_all_users_svc(db: AsyncSession) -> list[User]:
        return await UserCrud.get_all(db)

    @staticmethod
    async def update_user_svc(db: AsyncSession, user_id: int, data: UserUpdate) -> User:
        user = await UserCrud.get_user(db, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"user_id '{user_id}'에 해당하는 유저가 없습니다.")
        try:
            updated = await UserCrud.update_user(db, user, data)
            await db.commit()
            await db.refresh(updated)
            return updated
        except Exception:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="유저 수정에 실패했습니다.")

    @staticmethod
    async def update_password_svc(db: AsyncSession, current_user: User, data: UserPasswordUpdate) -> dict:
        if not verify_password(data.current_password, current_user.password):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="현재 비밀번호가 올바르지 않습니다.")
        if data.new_password != data.confirm_password:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="새 비밀번호가 일치하지 않습니다.")
        if verify_password(data.new_password, current_user.password):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="기존 비밀번호와 동일한 비밀번호는 사용할 수 없습니다.")
        try:
            current_user.password = get_password_hash(data.new_password)
            await db.commit()
            return {"message": "비밀번호 변경 완료"}
        except Exception:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="비밀번호 변경에 실패했습니다.")

    @staticmethod
    async def delete_user_svc(db: AsyncSession, user_id: int) -> dict:
        user = await UserCrud.get_user(db, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"user_id '{user_id}'에 해당하는 유저가 없습니다.")
        try:
            await UserCrud.delete_user(db, user)
            await db.commit()
            return {"message": f"user_id '{user_id}' 삭제 완료"}
        except Exception:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="유저 삭제에 실패했습니다.")

    @staticmethod
    async def login_svc(db: AsyncSession, data: UserLogin):
        user = await UserCrud.get_by_email(db, data.email)
        if not user or not verify_password(data.password, user.password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="잘못된 이메일 혹은 비밀번호입니다.")
        access_token = create_access_token(user.user_id)
        refresh_token = create_refresh_token(user.user_id)
        await UserCrud.update_refresh_token(db, user.user_id, refresh_token)
        await db.commit()
        await db.refresh(user)
        return user, access_token, refresh_token

    @staticmethod
    async def logout_svc(db: AsyncSession, user_id: int) -> None:
        await UserCrud.update_refresh_token(db, user_id, None)
        await db.commit()
