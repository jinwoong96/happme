from pydantic import BaseModel, EmailStr, Field, computed_field
from datetime import datetime
from typing import Optional, Literal

Provider = Literal["local", "google", "kakao", "naver"]

class UserCreate(BaseModel):
    name: Optional[str] = None
    email: EmailStr
    password: str
    provider: Provider = "local"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    profile_completed: Optional[bool] = None


class UserPasswordUpdate(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str


class UserRead(BaseModel):
    user_id: int
    name: Optional[str] = None
    email: Optional[str] = None
    provider: str
    role: str
    profile_completed: bool
    created_at: Optional[datetime] = None
    password: Optional[str] = Field(default=None, exclude=True)

    @computed_field
    @property
    def has_password(self) -> bool:
        return bool(self.password)

    class Config:
        from_attributes = True
