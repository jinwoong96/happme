"""
지원금 알림 탭의 "공고문 알림 받기" 키워드 CRUD + 매칭 알림 발송.

매칭은 새로 만들지 않고 이미 있는 AiClient.recommend_chat(user_profile, chat)을 그대로
재사용한다. 이 엔드포인트는 원래 채팅 기반 맞춤 추천용이지만, bene_ai가 벡터 유사도 검색
(BAAI/bge-m3)과 rule engine 자격 판정을 이미 같이 해주므로 "자유 텍스트 키워드 + 내 프로필
조건으로 지원 가능한 정책 찾기"에 그대로 들어맞는다.

호출 지점(둘 다 이 모듈의 check_and_notify_svc로 수렴):
  1) PolicyService.create_policy_svc / update_policy_svc - 관리자가 정책 1건을 만들거나
     고칠 때 즉시 체크.
  2) external_sync.run_refresh_all() 종료 시점 - 온통청년/복지로 배치 동기화(raw SQL이라
     ORM 훅을 못 탐)로 새로 들어오거나 바뀐 정책들을 한 번에 체크.
"""

import logging

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.db.crud.user import UserCrud
from app.db.crud.user_profile import UserProfileCrud
from app.db.crud.policy import PolicyCrud
from app.db.crud.user_alert_keyword import UserAlertKeywordCrud
from app.db.crud.notification import NotificationCrud
from app.db.scheme.user_alert_keyword import UserAlertKeywordCreate
from app.db.scheme.user_profile import UserProfileRead
from app.db.scheme.notification import NotificationCreate
from app.db.models.user_alert_keyword import UserAlertKeyword
from app.db.models.policy import Policy
from app.services.ai_client import AiClient

logger = logging.getLogger(__name__)

NOTIFY_TYPE = "KEYWORD_MATCH"


class UserAlertKeywordService:
    """알림 키워드 CRUD + 신규/변경 정책과의 매칭 체크 및 알림 발송."""

    # ---- 키워드 CRUD ----

    @staticmethod
    async def create_keyword_svc(db: AsyncSession, data: UserAlertKeywordCreate) -> UserAlertKeyword:
        """알림 키워드를 등록한다. 같은 유저가 같은 키워드를 이미 등록했으면 막는다."""
        if not await UserCrud.get_user(db, data.user_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="유저를 찾을 수 없습니다.")
        if await UserAlertKeywordCrud.get_by_user_keyword(db, data.user_id, data.keyword):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="이미 등록된 키워드입니다.")
        try:
            keyword = await UserAlertKeywordCrud.create_keyword(db, data)
            await db.commit()
            await db.refresh(keyword)
            return keyword
        except Exception:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="키워드 등록에 실패했습니다.")

    @staticmethod
    async def get_keywords_svc(db: AsyncSession, user_id: int) -> list[UserAlertKeyword]:
        return await UserAlertKeywordCrud.get_by_user(db, user_id)

    @staticmethod
    async def delete_keyword_svc(db: AsyncSession, keyword_id: int, user_id: int) -> dict:
        keyword = await UserAlertKeywordCrud.get_keyword(db, keyword_id)
        if not keyword:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="키워드를 찾을 수 없습니다.")
        if keyword.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="권한이 없습니다.")
        await UserAlertKeywordCrud.delete_keyword(db, keyword)
        await db.commit()
        return {"message": f"keyword_id '{keyword_id}' 삭제 완료"}

    # ---- 매칭 + 알림 발송 ----

    @staticmethod
    async def check_and_notify_since_svc(db: AsyncSession, since) -> int:
        """since(datetime) 이후 신규/변경된 정책들을 대상으로 키워드 매칭 알림을 생성."""
        changed_policies = await PolicyCrud.get_changed_since(db, since)
        return await UserAlertKeywordService.check_and_notify_svc(db, changed_policies)

    @staticmethod
    async def check_and_notify_svc(db: AsyncSession, target_policies: list[Policy]) -> int:
        """target_policies 중 등록된 알림 키워드와 매칭(bene_ai 유사도+자격판정)되는 것이
        있으면 Notification을 생성한다. 생성된 알림 개수를 반환."""
        target_policies = [p for p in target_policies if p.plcyNo]
        if not target_policies:
            return 0
        target_by_plcyno = {p.plcyNo: p for p in target_policies}

        keywords = await UserAlertKeywordCrud.get_all_active(db)
        if not keywords:
            return 0

        keywords_by_user: dict[int, list[str]] = {}
        for kw in keywords:
            keywords_by_user.setdefault(kw.user_id, []).append(kw.keyword)

        created = 0
        for user_id, user_keywords in keywords_by_user.items():
            profile = await UserProfileCrud.get_profile(db, user_id)
            if not profile:
                # 프로필 미등록 유저는 자격 판정을 할 수 없으므로 건너뜀
                continue
            profile_payload = UserProfileRead.model_validate(profile).model_dump(mode="json")

            for keyword_text in user_keywords:
                try:
                    result = await AiClient.recommend_chat(profile_payload, keyword_text)
                except HTTPException as e:
                    logger.warning("keyword_alert: AI 서버 호출 실패 (user_id=%s, keyword=%s): %s",
                                    user_id, keyword_text, e.detail)
                    continue

                matched_plcy_nos = UserAlertKeywordService._extract_plcy_nos(result)
                for plcy_no in matched_plcy_nos:
                    policy = target_by_plcyno.get(plcy_no)
                    if not policy:
                        continue

                    already_sent = await NotificationCrud.exists_today(
                        db, user_id=user_id, policy_id=policy.policy_id, notify_type=NOTIFY_TYPE
                    )
                    if already_sent:
                        continue

                    await NotificationCrud.create_notification(
                        db,
                        NotificationCreate(
                            user_id=user_id,
                            policy_id=policy.policy_id,
                            notify_type=NOTIFY_TYPE,
                            title=f"[{keyword_text}] 지원 가능한 공고문이 있어요",
                            content=f"등록하신 '{keyword_text}' 관련 '{policy.plcyNm}'에 지원 가능해요.",
                        ),
                    )
                    created += 1

        await db.commit()
        return created

    @staticmethod
    def _extract_plcy_nos(result) -> set[str]:
        """recommend_chat_svc 응답(버킷 키 -> 정책 리스트인 dict)에서 plcyNo만 뽑아낸다.
        버킷 구성이 바뀌어도(dict 형태만 유지되면) 그대로 동작한다."""
        plcy_nos: set[str] = set()
        if isinstance(result, dict):
            buckets = list(result.values())
        elif isinstance(result, list):
            buckets = [result]
        else:
            return plcy_nos

        for bucket in buckets:
            if not isinstance(bucket, list):
                continue
            for item in bucket:
                if isinstance(item, dict) and item.get("plcyNo"):
                    plcy_nos.add(str(item["plcyNo"]))
        return plcy_nos
