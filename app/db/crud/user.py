from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.user import User
from app.db.scheme.user import UserCreate, UserUpdate


class UserCrud:

    @staticmethod
    async def create_user(db: AsyncSession, data: UserCreate) -> User:
        user = User(**data.model_dump())
        db.add(user)
        await db.flush()
        return user

    @staticmethod
    async def get_user(db: AsyncSession, user_id: int) -> User | None:
        result = await db.execute(select(User).where(User.user_id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> User | None:
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_email_and_provider(db: AsyncSession, email: str, provider: str) -> User | None:
        result = await db.execute(
            select(User).where(User.email == email, User.provider == provider)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all(db: AsyncSession) -> list[User]:
        result = await db.execute(select(User))
        return list(result.scalars().all())

    @staticmethod
    async def update_user(db: AsyncSession, user: User, data: UserUpdate) -> User:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(user, key, value)
        await db.flush()
        return user

    @staticmethod
    async def update_refresh_token(db: AsyncSession, user_id: int, refresh_token: str | None) -> User | None:
        user = await db.get(User, user_id)
        if user:
            user.refresh_token = refresh_token
            await db.flush()
        return user

    @staticmethod
    async def delete_user(db: AsyncSession, user: User) -> None:
        await db.delete(user)
        await db.flush()
