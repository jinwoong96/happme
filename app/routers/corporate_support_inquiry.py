from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.db.scheme.corporate_support_inquiry import CorporateSupportInquiryCreate, CorporateSupportInquiryAnswer, CorporateSupportInquiryRead
from app.db.models.user import User
from app.services.corporate_support_inquiry import CorporateSupportInquiryService as corporate_support_inquiry_svc
from app.core.jwt_handle import get_current_user

router = APIRouter(prefix="/corporate-support-inquiries", tags=["CorporateSupportInquiry"])


# C 문의 생성 (user_id는 body 값을 신뢰하지 않고 로그인 유저로 강제)
@router.post("/", response_model=CorporateSupportInquiryRead, status_code=201)
async def create_corporate_support_inquiry(data: CorporateSupportInquiryCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    data.user_id = current_user.user_id
    return await corporate_support_inquiry_svc.create_inquiry_svc(db, data)


# R 전체 조회 (관리자용)
@router.get("/", response_model=list[CorporateSupportInquiryRead])
async def get_all_corporate_support_inquiries(db: AsyncSession = Depends(get_db)):
    return await corporate_support_inquiry_svc.get_all_inquiries_svc(db)


# R 내 문의 조회
@router.get("/me", response_model=list[CorporateSupportInquiryRead])
async def get_my_corporate_support_inquiries(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await corporate_support_inquiry_svc.get_my_inquiries_svc(db, current_user.user_id)


# R 단일 조회
@router.get("/{inquiry_id}", response_model=CorporateSupportInquiryRead)
async def get_corporate_support_inquiry(inquiry_id: int, db: AsyncSession = Depends(get_db)):
    return await corporate_support_inquiry_svc.get_inquiry_svc(db, inquiry_id)


# U 답변 등록 (관리자용)
@router.patch("/{inquiry_id}/answer", response_model=CorporateSupportInquiryRead)
async def answer_corporate_support_inquiry(inquiry_id: int, data: CorporateSupportInquiryAnswer, db: AsyncSession = Depends(get_db)):
    return await corporate_support_inquiry_svc.answer_inquiry_svc(db, inquiry_id, data.answer)


# D 삭제
@router.delete("/{inquiry_id}")
async def delete_corporate_support_inquiry(inquiry_id: int, db: AsyncSession = Depends(get_db)):
    return await corporate_support_inquiry_svc.delete_inquiry_svc(db, inquiry_id)
