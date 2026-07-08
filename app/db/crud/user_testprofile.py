from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user_testprofile import UserTestProfile
from app.db.scheme.user_testprofile import UserTestProfileCreate


class UserTestProfileCrud:

    @staticmethod
    async def create_test_profile(db: AsyncSession, data: UserTestProfileCreate) -> UserTestProfile:
        test_profile = UserTestProfile(**data.model_dump())
        db.add(test_profile)
        await db.flush()
        await db.refresh(test_profile)
        return test_profile
