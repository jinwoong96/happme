from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.db.scheme.ad_partnership_inquiry import AdPartnershipInquiryCreate, AdPartnershipInquiryAnswer, AdPartnershipInquiryRead
from app.db.models.user import User
from app.services.ad_partnership_inquiry import AdPartnershipInquiryService as ad_partnership_inquiry_svc
from app.core.jwt_handle import get_current_user

router = APIRouter(prefix="/ad-partnership-inquiries", tags=["AdPartnershipInquiry"])


# C 문의 생성 (user_id는 body 값을 신뢰하지 않고 로그인 유저로 강제)
@router.post("/", response_model=AdPartnershipInquiryRead, status_code=201)
async def create_ad_partnership_inquiry(data: AdPartnershipInquiryCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    data.user_id = current_user.user_id
    return await ad_partnership_inquiry_svc.create_inquiry_svc(db, data)


# R 전체 조회 (관리자용)
@router.get("/", response_model=list[AdPartnershipInquiryRead])
async def get_all_ad_partnership_inquiries(db: AsyncSession = Depends(get_db)):
    return await ad_partnership_inquiry_svc.get_all_inquiries_svc(db)


# R 내 문의 조회
@router.get("/me", response_model=list[AdPartnershipInquiryRead])
async def get_my_ad_partnership_inquiries(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await ad_partnership_inquiry_svc.get_my_inquiries_svc(db, current_user.user_id)


# R 단일 조회
@router.get("/{inquiry_id}", response_model=AdPartnershipInquiryRead)
async def get_ad_partnership_inquiry(inquiry_id: int, db: AsyncSession = Depends(get_db)):
    return await ad_partnership_inquiry_svc.get_inquiry_svc(db, inquiry_id)


# U 답변 등록 (관리자용)
@router.patch("/{inquiry_id}/answer", response_model=AdPartnershipInquiryRead)
async def answer_ad_partnership_inquiry(inquiry_id: int, data: AdPartnershipInquiryAnswer, db: AsyncSession = Depends(get_db)):
    return await ad_partnership_inquiry_svc.answer_inquiry_svc(db, inquiry_id, data.answer)


# D 삭제
@router.delete("/{inquiry_id}")
async def delete_ad_partnership_inquiry(inquiry_id: int, db: AsyncSession = Depends(get_db)):
    return await ad_partnership_inquiry_svc.delete_inquiry_svc(db, inquiry_id)
