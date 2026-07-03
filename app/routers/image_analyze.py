import os
import uuid

from fastapi import APIRouter, UploadFile, File, HTTPException, Request

from app.core.settings import settings
from app.services.image_analyze.analyze import ImageAnalyzeService

router = APIRouter(prefix="/image-analyze", tags=["ImageAnalyze"])


def get_image_analyze_service(request: Request) -> ImageAnalyzeService:
    return request.app.state.image_analyze_service


# C 이미지 분석 (탐지 -> OCR -> 정책 검색 -> LLM 요약)
@router.post("/")
async def analyze_image(request: Request, file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="이미지 파일만 업로드 가능합니다.")

    image_analyze_service = get_image_analyze_service(request)

    tmp_path = os.path.join(settings.temp_upload_dir, f"{uuid.uuid4().hex}_{file.filename}")
    try:
        content = await file.read()
        with open(tmp_path, "wb") as f:
            f.write(content)
        return image_analyze_service.analyze_svc(tmp_path)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


# R 헬스체크
@router.get("/health")
async def health_check(request: Request):
    loaded = hasattr(request.app.state, "image_analyze_service")
    return {"status": "ok", "image_analyze_service_loaded": loaded}