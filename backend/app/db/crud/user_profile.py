from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.user_profile import UserProfile
from app.db.scheme.user_profile import UserProfileCreate, UserProfileUpdate


class UserProfileCrud:
    """사용자 프로필(user_profile, 추천에 쓰이는 나이/지역/학력 등)에 대한 생성/조회/수정/삭제."""

    @staticmethod
    async def create_profile(db: AsyncSession, data: UserProfileCreate) -> UserProfile:
        profile = UserProfile(**data.model_dump())
        db.add(profile)
        await db.flush()
        return profile

    @staticmethod
    async def get_profile(db: AsyncSession, user_id: int) -> UserProfile | None:
        result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def update_profile(db: AsyncSession, profile: UserProfile, data: UserProfileUpdate) -> UserProfile:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(profile, key, value)
        await db.flush()
        return profile

    @staticmethod
    async def delete_profile(db: AsyncSession, profile: UserProfile) -> None:
        await db.delete(profile)
        await db.flush()
