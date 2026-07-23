from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from app.core.settings import settings

async_engine = create_async_engine(settings.db_url, echo=False)

AsyncSessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

sync_engine = create_engine(settings.sync_db_url, pool_pre_ping=True)

Base = declarative_base()


async def get_db():
    """요청마다 DB 세션을 하나 열어주는 FastAPI 의존성. 예외가 나면 롤백하고,
    요청이 끝나면 세션을 닫는다."""
    session = AsyncSessionLocal()
    try:
        yield session
    except Exception:
        try:
            await session.rollback()
        except Exception:
            pass
        raise
    finally:
        try:
            await session.close()
        except Exception:
            pass
