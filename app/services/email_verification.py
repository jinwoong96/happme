import random
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.core.settings import settings
from app.db.crud.email_verification import EmailVerificationCrud
from app.db.crud.user import UserCrud
from app.db.scheme.email_verification import EmailVerificationSend, EmailVerificationConfirm


def _generate_code() -> str:
    return f"{random.randint(0, 999999):06d}"


def _send_email(to_email: str, code: str) -> None:
    subject = "[BENE] 이메일 인증번호 안내"
    body = (
        f"안녕하세요, BENE 입니다.\n\n"
        f"요청하신 인증번호는 [{code}] 입니다.\n"
        f"인증번호는 발급 후 {settings.email_code_expire_seconds // 60}분간 유효합니다.\n\n"
        f"본인이 요청하지 않았다면 이 메일을 무시해주세요."
    )
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from or settings.smtp_user
    msg["To"] = to_email

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(msg["From"], [to_email], msg.as_string())
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="인증 메일 발송에 실패했습니다. 잠시 후 다시 시도해주세요.",
        )


class EmailVerificationService:

    @staticmethod
    async def send_code_svc(db: AsyncSession, data: EmailVerificationSend) -> dict:
        if await UserCrud.get_by_email(db, data.email):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="이미 사용 중인 이메일입니다.")

        code = _generate_code()
        expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(
            seconds=settings.email_code_expire_seconds
        )

        try:
            await EmailVerificationCrud.create_verification(db, data.email, code, expires_at)
            await db.commit()
        except Exception:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="인증번호 발급에 실패했습니다.")

        _send_email(data.email, code)
        return {"message": "인증번호가 이메일로 전송되었습니다."}

    @staticmethod
    async def verify_code_svc(db: AsyncSession, data: EmailVerificationConfirm) -> dict:
        ev = await EmailVerificationCrud.get_latest_by_email(db, data.email)
        if not ev:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="인증번호를 먼저 요청해주세요.")
        if ev.expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="인증번호가 만료되었습니다. 다시 요청해주세요.")
        if ev.code != data.code:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="인증번호가 일치하지 않습니다.")

        try:
            await EmailVerificationCrud.mark_verified(db, ev)
            await db.commit()
        except Exception:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="인증 처리에 실패했습니다.")

        return {"message": "이메일 인증이 완료되었습니다."}

    @staticmethod
    async def ensure_verified(db: AsyncSession, email: str) -> None:
        """회원가입 직전, 해당 이메일이 인증 완료되었는지 확인"""
        ev = await EmailVerificationCrud.get_latest_by_email(db, email)
        if not ev or not ev.is_verified:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="이메일 인증을 먼저 완료해주세요.")