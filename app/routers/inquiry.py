from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.db.scheme.inquiry import InquiryCreate, InquiryAnswer, InquiryRead
from app.db.models.user import User
from app.services.inquiry import InquiryService as inquiry_svc
from app.core.jwt_handle import get_current_user

router = APIRouter(prefix="/inquiries", tags=["Inquiry"])


# C 문의 생성
@router.post("/", response_model=InquiryRead, status_code=201)
async def create_inquiry(data: InquiryCreate, db: AsyncSession = Depends(get_db)):
    return await inquiry_svc.create_inquiry_svc(db, data)


# R 전체 조회 (관리자용)
@router.get("/", response_model=list[InquiryRead])
async def get_all_inquiries(db: AsyncSession = Depends(get_db)):
    return await inquiry_svc.get_all_inquiries_svc(db)


# R 내 문의 조회
@router.get("/me", response_model=list[InquiryRead])
async def get_my_inquiries(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await inquiry_svc.get_my_inquiries_svc(db, current_user.user_id)


# R 단일 조회
@router.get("/{inquiry_id}", response_model=InquiryRead)
async def get_inquiry(inquiry_id: int, db: AsyncSession = Depends(get_db)):
    return await inquiry_svc.get_inquiry_svc(db, inquiry_id)


# U 답변 등록 (관리자용)
@router.patch("/{inquiry_id}/answer", response_model=InquiryRead)
async def answer_inquiry(inquiry_id: int, data: InquiryAnswer, db: AsyncSession = Depends(get_db)):
    return await inquiry_svc.answer_inquiry_svc(db, inquiry_id, data.answer)


# D 삭제
@router.delete("/{inquiry_id}")
async def delete_inquiry(inquiry_id: int, db: AsyncSession = Depends(get_db)):
    return await inquiry_svc.delete_inquiry_svc(db, inquiry_id)
