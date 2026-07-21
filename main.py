import os
import sys

# pip로 설치된 nvidia-cublas-cu13 등은 site-packages 안에 DLL을 두지만 Windows PATH에는
# 자동으로 잡히지 않아 paddlepaddle-gpu가 cublas64_13.dll 등을 못 찾는 문제가 생긴다.
# paddle 내부 로더는 os.add_dll_directory가 아니라 PATH 환경변수를 직접 참조하므로
# GPU 관련 모듈(paddleocr 등)을 import하기 전에 PATH에 해당 DLL 폴더를 추가해준다.
if sys.platform == "win32":
    try:
        import nvidia
        _nvidia_dir = os.path.dirname(nvidia.__file__)
        _dll_dirs = [
            os.path.join(_nvidia_dir, *_sub.split("/"))
            for _sub in ("cu13/bin/x86_64", "cudnn/bin")
        ]
        _dll_dirs = [d for d in _dll_dirs if os.path.isdir(d)]
        if _dll_dirs:
            os.environ["PATH"] = os.pathsep.join(_dll_dirs) + os.pathsep + os.environ["PATH"]
    except ImportError:
        pass

import uvicorn
import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.concurrency import asynccontextmanager
from app.core.settings import settings
from app.core.logging_config import setup_logging
from app.core.slack_alert import send_slack_alert
from app.core.model_downloader import ensure_models_downloaded
from app.core.data_downloader import ensure_data_downloaded

from app.services.image_analyze.detection import DetectionService
from app.services.image_analyze.ocr import OcrService
from app.services.image_analyze.search import SearchService
from app.services.image_analyze.llm import LlmService
from app.services.image_analyze.analyze import ImageAnalyzeService

from app.services.recommendation.policy_loader import PolicyLoaderService
from app.services.recommendation.region_matcher import RegionMatcher
from app.services.recommendation.eligibility_rules import PolicyEligibilityEngine
from app.services.recommendation.similarity_search import PolicySimilarityService
from app.services.recommendation.recommendation_service import RecommendationService
from app.services.recommendation.scenario_resolver import ScenarioResolver
from app.services.recommendation.income_eligibility import IncomeEligibilityService
from app.services.schedule_extract import ScheduleService

from app.services.policy_summary.pdf_summary import PdfSummaryService
from app.services.policy_summary.web_summary import WebSummaryService

from app.routers.policy_summary import router as policy_summary_router
from app.routers.image_analyze import router as image_analyze_router
from app.routers.recommendation import router as recommendation_router
from app.routers.policy_dedup import router as policy_dedup_router
from app.routers.search_docs import router as search_docs_router
from app.routers.policy_cache import router as policy_cache_router

from app.routers.schedule import router as schedule_router

setup_logging(settings.log_dir)

if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.sentry_environment or settings.app_env,
        traces_sample_rate=1.0,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 무거운 모델들은 서버 시작 시 한 번만 로드합니다.
    print("[bene_ai] 모델 로드 시작...")

    ensure_models_downloaded()  # 로컬에 없으면 S3에서 자동 다운로드
    ensure_data_downloaded()  # 정책 원본/임베딩 캐시가 로컬에 없으면 S3에서 자동 다운로드

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

    app.state.pdf_summary_service = PdfSummaryService()
    app.state.web_summary_service = WebSummaryService(app.state.pdf_summary_service)

    # app.state.schedule_service = ScheduleService()

    policy_loader = PolicyLoaderService()
    app.state.policy_loader = policy_loader
    policy_similarity_service = PolicySimilarityService()
    app.state.policy_similarity_service = policy_similarity_service
    app.state.recommendation_service = RecommendationService(
        policy_loader=policy_loader,
        eligibility_engine=PolicyEligibilityEngine(region_matcher=RegionMatcher()),
        similarity_service=policy_similarity_service,
    )
    # watsonx 연결은 새로 만들지 않고 pdf_summary_service의 llm_model을 재사용한다.
    app.state.income_eligibility_service = IncomeEligibilityService(
        policy_loader=policy_loader,
        llm_service=app.state.pdf_summary_service,
    )
    app.state.scenario_resolver = ScenarioResolver()
    app.state.schedule_service = ScheduleService()

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
app.include_router(recommendation_router)
app.include_router(schedule_router)
app.include_router(policy_summary_router)
app.include_router(policy_dedup_router)
app.include_router(search_docs_router)
app.include_router(policy_cache_router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    sentry_sdk.capture_exception(exc)
    await send_slack_alert(request, exc)
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8090, reload=True)
