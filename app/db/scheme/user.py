from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class UserCreate(BaseModel):
    name: Optional[str] = None
    email: EmailStr
    password: str


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
    role: str
    profile_completed: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
