from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.db.scheme.pdf_summary import PdfSummaryCreate, PdfSummaryRead, PdfMatchCreate
from app.db.models.user import User
from app.services.pdf_summary import PdfSummaryService as pdf_svc
from app.core.jwt_handle import get_current_user

router = APIRouter(prefix="/pdf", tags=["PdfSummary"])


# C PDF 요약 저장
@router.post("/", response_model=PdfSummaryRead, status_code=201)
async def create_pdf(data: PdfSummaryCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await pdf_svc.create_pdf_svc(db, data)


# C 매칭 추가
@router.post("/matches", status_code=201)
async def add_match(data: PdfMatchCreate, db: AsyncSession = Depends(get_db)):
    return await pdf_svc.add_match_svc(db, data)


# R 내 PDF 목록
@router.get("/me", response_model=list[PdfSummaryRead])
async def get_my_pdfs(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await pdf_svc.get_by_user_svc(db, current_user.user_id)


# R 단일 조회
@router.get("/{pdf_id}", response_model=PdfSummaryRead)
async def get_pdf(pdf_id: int, db: AsyncSession = Depends(get_db)):
    return await pdf_svc.get_pdf_svc(db, pdf_id)


# D 삭제
@router.delete("/{pdf_id}")
async def delete_pdf(pdf_id: int, db: AsyncSession = Depends(get_db)):
    return await pdf_svc.delete_pdf_svc(db, pdf_id)
