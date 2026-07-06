from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.db.crud.user_profile import UserProfileCrud
from app.db.crud.user import UserCrud
from app.db.scheme.user_profile import UserProfileCreate, UserProfileUpdate
from app.db.models.user_profile import UserProfile
from app.db.models.user import User


class UserProfileService:

    @staticmethod
    async def _require_user(db: AsyncSession, user_id: int) -> User:
        user = await UserCrud.get_user(db, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"user_id '{user_id}'에 해당하는 유저가 없습니다.")
        return user

    @staticmethod
    async def create_profile_svc(db: AsyncSession, data: UserProfileCreate) -> UserProfile:
        await UserProfileService._require_user(db, data.user_id)
        if await UserProfileCrud.get_profile(db, data.user_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="이미 프로필이 존재합니다. 수정을 사용하세요.")
        try:
            profile = await UserProfileCrud.create_profile(db, data)
            # profile_completed 플래그 업데이트
            user = await UserCrud.get_user(db, data.user_id)
            user.profile_completed = True
            await db.commit()
            await db.refresh(profile)
            return profile
        except Exception:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="프로필 생성에 실패했습니다.")

    @staticmethod
    async def get_profile_svc(db: AsyncSession, user_id: int) -> UserProfile:
        profile = await UserProfileCrud.get_profile(db, user_id)
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"user_id '{user_id}'에 해당하는 프로필이 없습니다.")
        return profile

    @staticmethod
    async def update_profile_svc(db: AsyncSession, user_id: int, data: UserProfileUpdate) -> UserProfile:
        profile = await UserProfileCrud.get_profile(db, user_id)
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"user_id '{user_id}'에 해당하는 프로필이 없습니다.")
        try:
            updated = await UserProfileCrud.update_profile(db, profile, data)
            await db.commit()
            await db.refresh(updated)
            return updated
        except Exception:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="프로필 수정에 실패했습니다.")

    @staticmethod
    async def upsert_profile_svc(db: AsyncSession, user_id: int, data: UserProfileUpdate) -> UserProfile:
        await UserProfileService._require_user(db, user_id)
        profile = await UserProfileCrud.get_profile(db, user_id)
        try:
            if profile:
                updated = await UserProfileCrud.update_profile(db, profile, data)
            else:
                create_data = UserProfileCreate(user_id=user_id, **data.model_dump(exclude_unset=True))
                updated = await UserProfileCrud.create_profile(db, create_data)
                user = await UserCrud.get_user(db, user_id)
                user.profile_completed = True
            await db.commit()
            await db.refresh(updated)
            return updated
        except Exception:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="프로필 저장에 실패했습니다.")

    @staticmethod
    async def delete_profile_svc(db: AsyncSession, user_id: int) -> dict:
        profile = await UserProfileCrud.get_profile(db, user_id)
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"user_id '{user_id}'에 해당하는 프로필이 없습니다.")
        try:
            await UserProfileCrud.delete_profile(db, profile)
            user = await UserCrud.get_user(db, user_id)
            if user:
                user.profile_completed = False
            await db.commit()
            return {"message": f"user_id '{user_id}' 프로필 삭제 완료"}
        except Exception:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="프로필 삭제에 실패했습니다.")
