from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.db.models.email_verification import EmailVerification


class EmailVerificationCrud:
    """이메일 인증코드(email_verification) 테이블에 대한 생성/조회/인증완료 처리/삭제."""

    @staticmethod
    async def create_verification(db: AsyncSession, email: str, code: str, expires_at) -> EmailVerification:
        """인증코드를 새로 발급한다. 같은 이메일로 이미 발급된 코드가 있으면 먼저 지운다."""
        # 같은 이메일로 발급된 기존 인증 요청은 모두 정리
        await db.execute(delete(EmailVerification).where(EmailVerification.email == email))
        ev = EmailVerification(email=email, code=code, expires_at=expires_at, is_verified=False)
        db.add(ev)
        await db.flush()
        return ev

    @staticmethod
    async def get_latest_by_email(db: AsyncSession, email: str) -> EmailVerification | None:
        result = await db.execute(
            select(EmailVerification)
            .where(EmailVerification.email == email)
            .order_by(EmailVerification.id.desc())
        )
        return result.scalars().first()

    @staticmethod
    async def mark_verified(db: AsyncSession, ev: EmailVerification) -> EmailVerification:
        ev.is_verified = True
        await db.flush()
        return ev

    @staticmethod
    async def delete_by_email(db: AsyncSession, email: str) -> None:
        await db.execute(delete(EmailVerification).where(EmailVerification.email == email))