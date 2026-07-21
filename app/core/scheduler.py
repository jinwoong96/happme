"""
백그라운드 스케줄러(APScheduler) 설정.

앱의 lifespan과 생명주기를 같이 해야 하는 주기 작업들을 여기서 등록한다.
main.py는 start_scheduler()/stop_scheduler()만 호출하고, job의 내용은 몰라도 되도록 분리.
"""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.db.database import AsyncSessionLocal
from app.services.deadline_alert import run_deadline_alerts

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone="Asia/Seoul")


async def _run_deadline_alerts_job():
    """스케줄러가 호출하는 job. 요청 스코프가 없으므로 세션을 직접 열고 닫는다."""
    async with AsyncSessionLocal() as session:
        try:
            await run_deadline_alerts(session)
        except Exception:
            await session.rollback()
            logger.exception("deadline_alert job 실행 중 오류")


def start_scheduler() -> None:
    """앱 시작 시(lifespan) 호출. job 등록 + 스케줄러 시작."""
    # 매일 오전 9시(KST)에 마감 하루 전 즐겨찾기 알림을 생성
    scheduler.add_job(
        _run_deadline_alerts_job,
        CronTrigger(hour=9, minute=0),
        id="deadline_alerts",
        replace_existing=True,
    )
    scheduler.start()


def stop_scheduler() -> None:
    """앱 종료 시(lifespan) 호출."""
    scheduler.shutdown(wait=False)