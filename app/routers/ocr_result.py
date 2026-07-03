from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.db.scheme.ocr_result import OcrResultCreate, OcrResultRead, OcrMatchCreate
from app.db.models.user import User
from app.services.ocr_result import OcrResultService as ocr_svc
from app.core.jwt_handle import get_current_user

router = APIRouter(prefix="/ocr", tags=["OcrResult"])


# C OCR 결과 저장
@router.post("/", response_model=OcrResultRead, status_code=201)
async def create_ocr(data: OcrResultCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await ocr_svc.create_ocr_svc(db, data)
 
 
# C 이미지 업로드 -> bene_ai 분석(탐지+OCR+정책검색+LLM) -> OCR 결과 저장까지 한 번에
@router.post("/analyze-image")
async def analyze_image(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    image_bytes = await file.read()
    return await ocr_svc.analyze_image_svc(db, current_user.user_id, image_bytes, file.filename, file.content_type)


# C 매칭 추가
@router.post("/matches", status_code=201)
async def add_match(data: OcrMatchCreate, db: AsyncSession = Depends(get_db)):
    return await ocr_svc.add_match_svc(db, data)


# R 내 OCR 목록
@router.get("/me", response_model=list[OcrResultRead])
async def get_my_ocr(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await ocr_svc.get_by_user_svc(db, current_user.user_id)


# R 단일 조회
@router.get("/{ocr_id}", response_model=OcrResultRead)
async def get_ocr(ocr_id: int, db: AsyncSession = Depends(get_db)):
    return await ocr_svc.get_ocr_svc(db, ocr_id)


# D 삭제
@router.delete("/{ocr_id}")
async def delete_ocr(ocr_id: int, db: AsyncSession = Depends(get_db)):
    return await ocr_svc.delete_ocr_svc(db, ocr_id)
