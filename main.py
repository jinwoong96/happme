import uvicorn
import sentry_sdk
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.concurrency import asynccontextmanager

from app.core.settings import settings
from app.core.logging_config import setup_logging
from app.core.slack_alert import send_slack_alert
from app.core.request_context import set_request_id, new_request_id, REQUEST_ID_HEADER
from app.db.database import Base, async_engine, AsyncSessionLocal
from app.db.seed import run_all_seeds
from app.middleware.token_refresh import RefreshTokenMiddleware
from app.core.scheduler import start_scheduler, stop_scheduler

from app.routers.user import router as user_router
from app.routers.email_verification import router as email_verification_router
from app.routers.google_auth import router as google_auth_router
from app.routers.kakao_auth import router as kakao_auth_router
from app.routers.naver_auth import router as naver_auth_router
from app.routers.user_profile import router as user_profile_router
from app.routers.policy import router as policy_router
from app.routers.bookmark import router as bookmark_router
from app.routers.notification import router as notification_router
from app.routers.inquiry import router as inquiry_router
from app.routers.ad_partnership_inquiry import router as ad_partnership_inquiry_router
from app.routers.corporate_support_inquiry import router as corporate_support_inquiry_router
from app.routers.notice import router as notice_router
from app.routers.simulation_result import router as simulation_router
from app.routers.ocr_result import router as ocr_router
from app.routers.pdf_summary import router as pdf_router
from app.routers.code_master import router as code_router
from app.routers.recommendation import router as recommendation_router
from app.routers.local_program import router as local_program_router
from app.routers.user_alert_keyword import router as user_alert_keyword_router

load_dotenv(dotenv_path=".env")

setup_logging()

if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.sentry_environment or settings.app_env,
        traces_sample_rate=1.0,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await run_all_seeds(session)

    start_scheduler()

    yield

    stop_scheduler()
    await async_engine.dispose()


app = FastAPI(title="BENE 청년정책 서비스", lifespan=lifespan)

app.add_middleware(RefreshTokenMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5174",
        "http://localhost:5173",
        "http://localhost:4173",
        "https://sub-m2com.com",
        "https://www.sub-m2com.com", 
        "https://admin.sub-m2com.com",
    ],
    allow_origin_regex=r"https://.*\.ngrok-free\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """여러 요청이 동시에 들어와도(그리고 backend->ai로 넘어가도) 로그로 한 요청의
    흐름을 끝까지 따라갈 수 있도록, 요청마다 request_id를 부여해 응답 헤더로도 돌려준다.
    ai 서버가 이미 만든 request_id로 넘어온 경우(반대로 ai가 먼저 만든 걸 이어받는 경우는
    현재 흐름상 없지만 대비)엔 그 값을 그대로 이어받는다."""
    request_id = request.headers.get(REQUEST_ID_HEADER) or new_request_id()
    set_request_id(request_id)
    sentry_sdk.set_tag("request_id", request_id)
    response = await call_next(request)
    response.headers[REQUEST_ID_HEADER] = request_id
    return response


app.include_router(user_router)
app.include_router(email_verification_router)
app.include_router(google_auth_router)
app.include_router(kakao_auth_router)
app.include_router(naver_auth_router)
app.include_router(user_profile_router)
app.include_router(policy_router)
app.include_router(bookmark_router)
app.include_router(notification_router)
app.include_router(inquiry_router)
app.include_router(ad_partnership_inquiry_router)
app.include_router(corporate_support_inquiry_router)
app.include_router(notice_router)
app.include_router(simulation_router)
app.include_router(ocr_router)
app.include_router(pdf_router)
app.include_router(code_router)
app.include_router(recommendation_router)
app.include_router(local_program_router)
app.include_router(user_alert_keyword_router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    sentry_sdk.capture_exception(exc)
    await send_slack_alert(request, exc)
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8082, reload=True,
                proxy_headers=True, forwarded_allow_ips="*")