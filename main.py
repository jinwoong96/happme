import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import asynccontextmanager

from app.db.database import Base, async_engine, AsyncSessionLocal
from app.db.seed import run_all_seeds
from app.middleware.token_refresh import RefreshTokenMiddleware

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
from app.routers.notice import router as notice_router
from app.routers.simulation_result import router as simulation_router
from app.routers.ocr_result import router as ocr_router
from app.routers.pdf_summary import router as pdf_router
from app.routers.code_master import router as code_router
from app.routers.recommendation import router as recommendation_router

load_dotenv(dotenv_path=".env")


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await run_all_seeds(session)
    yield
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
        "http://localhost:5173",
        "http://d26uutajlu47ap.cloudfront.net", 
    ],
    allow_origin_regex=r"https://.*\.ngrok-free\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
app.include_router(notice_router)
app.include_router(simulation_router)
app.include_router(ocr_router)
app.include_router(pdf_router)
app.include_router(code_router)
app.include_router(recommendation_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8082, reload=True,
                proxy_headers=True, forwarded_allow_ips="*")
