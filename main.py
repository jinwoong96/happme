import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import asynccontextmanager
from app.core.model_downloader import ensure_models_downloaded

from app.services.image_analyze.detection import DetectionService
from app.services.image_analyze.ocr import OcrService
from app.services.image_analyze.search import SearchService
from app.services.image_analyze.llm import LlmService
from app.services.image_analyze.analyze import ImageAnalyzeService

from app.routers.image_analyze import router as image_analyze_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 무거운 모델들은 서버 시작 시 한 번만 로드합니다.
    print("[bene_ai] 모델 로드 시작...")

    ensure_models_downloaded()  # 로컬에 없으면 S3에서 자동 다운로드

    detection_service = DetectionService()
    ocr_service = OcrService()
    search_service = SearchService()
    llm_service = LlmService()

    app.state.image_analyze_service = ImageAnalyzeService(
        detection_service=detection_service,
        ocr_service=ocr_service,
        search_service=search_service,
        llm_service=llm_service,
    )

    print("[bene_ai] 모든 모델 로드 완료, 서비스 준비됨")
    yield


app = FastAPI(title="BENE AI 분석 서비스", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 내부망에서 bene_backend만 호출하는 서비스이므로 전체 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(image_analyze_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8090, reload=True)