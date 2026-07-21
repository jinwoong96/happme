"""
즐겨찾기 마감 하루 전 알림 배치.

즐겨찾기(Bookmark)에서 알림(alarm_yn=True)을 켜둔 정책 중, 마감일(Policy.aplyEndDt)이
내일인 것을 찾아 사용자에게 notify_type="BOOKMARK" 알림을 생성한다.

매일 1회(main.py의 스케줄러) 실행되는 것을 전제로 하며, 같은 날 중복 실행되더라도
(재시작 등) NotificationCrud.exists_today로 같은 유저+정책 알림이 이미 있으면 건너뛴다.
"""

import logging
from datetime import date, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.crud.bookmark import BookmarkCrud
from app.db.crud.notification import NotificationCrud
from app.db.scheme.notification import NotificationCreate

logger = logging.getLogger(__name__)

KST = ZoneInfo("Asia/Seoul")
NOTIFY_TYPE = "BOOKMARK"


async def run_deadline_alerts(db: AsyncSession, target_date: date | None = None) -> int:
    """target_date가 마감일인 알림-on 즐겨찾기에 대해 알림을 생성하고, 생성한 개수를 반환.
    target_date를 안 주면 '내일(KST 기준)'을 사용한다."""
    if target_date is None:
        target_date = _tomorrow_kst()

    targets = await BookmarkCrud.get_alarm_targets_by_deadline(db, target_date)

    created = 0
    for bookmark in targets:
        policy = bookmark.policy
        if policy is None:
            continue

        already_sent = await NotificationCrud.exists_today(
            db, user_id=bookmark.user_id, policy_id=policy.policy_id, notify_type=NOTIFY_TYPE
        )
        if already_sent:
            continue

        await NotificationCrud.create_notification(
            db,
            NotificationCreate(
                user_id=bookmark.user_id,
                policy_id=policy.policy_id,
                notify_type=NOTIFY_TYPE,
                title=f"[마감 D-1] {policy.plcyNm}",
                content="즐겨찾기하신 정책의 신청 마감이 내일까지예요. 서둘러 확인해보세요!",
            ),
        )
        created += 1

    await db.commit()
    logger.info("deadline_alert: target_date=%s, bookmarks_checked=%d, notifications_created=%d",
                target_date, len(targets), created)
    return created


def _tomorrow_kst() -> date:
    from datetime import datetime
    return datetime.now(KST).date() + timedelta(days=1)