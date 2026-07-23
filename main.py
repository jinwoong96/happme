import os
import sys


import uvicorn
import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.concurrency import asynccontextmanager
from app.core.settings import settings
from app.core.logging_config import setup_logging
from app.core.slack_alert import send_slack_alert
from app.core.request_context import set_request_id, new_request_id, REQUEST_ID_HEADER
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
from app.services.recommendation.rule_engine_cache import RuleEngineCache
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
    rule_engine_cache = RuleEngineCache()
    app.state.rule_engine_cache = rule_engine_cache
    # watsonx 연결은 새로 만들지 않고 pdf_summary_service의 llm_model을 재사용한다.
    app.state.recommendation_service = RecommendationService(
        policy_loader=policy_loader,
        eligibility_engine=PolicyEligibilityEngine(region_matcher=RegionMatcher()),
        similarity_service=policy_similarity_service,
        llm_service=app.state.pdf_summary_service,
        rule_engine_cache=rule_engine_cache,
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


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """backend가 호출할 때 넘겨준 X-Request-Id를 그대로 이어받아서, backend->ai로
    넘어오는 하나의 요청 흐름을 로그로 계속 따라갈 수 있게 한다. 헤더가 없으면(직접
    호출 등) 새로 하나 만든다."""
    request_id = request.headers.get(REQUEST_ID_HEADER) or new_request_id()
    set_request_id(request_id)
    sentry_sdk.set_tag("request_id", request_id)
    response = await call_next(request)
    response.headers[REQUEST_ID_HEADER] = request_id
    return response


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
