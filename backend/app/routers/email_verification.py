from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.db.scheme.email_verification import EmailVerificationSend, EmailVerificationConfirm
from app.services.email_verification import EmailVerificationService as email_svc

router = APIRouter(prefix="/email", tags=["EmailVerification"])


# 이메일 인증번호 발송
@router.post("/send-code")
async def send_code(data: EmailVerificationSend, db: AsyncSession = Depends(get_db)):
    return await email_svc.send_code_svc(db, data)


# 이메일 인증번호 확인
@router.post("/verify-code")
async def verify_code(data: EmailVerificationConfirm, db: AsyncSession = Depends(get_db)):
    return await email_svc.verify_code_svc(db, data)