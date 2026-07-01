from pydantic import BaseModel, EmailStr


class EmailVerificationSend(BaseModel):
    email: EmailStr


class EmailVerificationConfirm(BaseModel):
    email: EmailStr
    code: str