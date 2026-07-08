from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.db.crud.user_profile import UserProfileCrud
from app.db.crud.bookmark import BookmarkCrud
from app.db.crud.policy import PolicyCrud
from app.db.scheme.user_profile import UserProfileRead
from app.services.ai_client import AiClient
from app.services.policy import PolicyService

POLICY_LIST_KEYS = ("available_policies", "closed_policies", "expired_policies", "unavailable_policies")


class RecommendationService:

    @staticmethod
    async def get_recommendations_svc(db: AsyncSession, user_id: int) -> dict:
        user_profile_payload = await RecommendationService._get_user_profile_payload(db, user_id)

        # TODO(1차 테스트 이후): 추천 결과 DB 저장, updated_at 비교를 통한 캐시 재사용 로직 추가
        result = await AiClient.recommend(user_profile_payload)
        result = await RecommendationService._attach_policy_cards(db, result)
        result = await RecommendationService._attach_db_policy_ids(db, result)
        return await RecommendationService._attach_bookmark_flags(db, user_id, result)

    @staticmethod
    async def get_chat_recommendations_svc(db: AsyncSession, user_id: int, chat: str) -> dict:
        user_profile_payload = await RecommendationService._get_user_profile_payload(db, user_id)
        result = await AiClient.recommend_chat(user_profile_payload, chat)
        result = await RecommendationService._attach_policy_cards(db, result)
        result = await RecommendationService._attach_db_policy_ids(db, result)
        return await RecommendationService._attach_bookmark_flags(db, user_id, result)

    @staticmethod
    async def _get_user_profile_payload(db: AsyncSession, user_id: int) -> dict:
        profile = await UserProfileCrud.get_profile(db, user_id)
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="프로필을 먼저 등록해주세요.")
        return UserProfileRead.model_validate(profile).model_dump(mode="json")

    @staticmethod
    async def _attach_policy_cards(db: AsyncSession, result: dict) -> dict:
        """plcyNo 기준으로 PolicyService.get_policy_cards_svc의 카드 표시용 필드를 덧붙입니다."""
        plcy_nos = set()
        for key in POLICY_LIST_KEYS:
            for policy in result.get(key, []):
                plcy_no = policy.get("plcyNo")
                if plcy_no is not None:
                    plcy_nos.add(str(plcy_no))

        cards = await PolicyService.get_policy_cards_svc(db, list(plcy_nos))

        for key in POLICY_LIST_KEYS:
            for policy in result.get(key, []):
                card = cards.get(str(policy.get("plcyNo")))
                if not card:
                    continue

                if card.get("policy_name"):
                    policy["policy_name"] = card["policy_name"]
                if card.get("policy_summary"):
                    policy["policy_summary"] = card["policy_summary"]
                policy["apply_period_type"] = card.get("apply_period_type")
                policy["apply_period"] = card.get("apply_period")
                policy["target"] = card.get("target")
                policy["link"] = card.get("link")

        return result

    @staticmethod
    async def _attach_db_policy_ids(db: AsyncSession, result: dict) -> dict:
        """AI 응답의 plcyNo로 backend DB에서 실제 policy_id를 조회해 각 정책 dict에 붙입니다."""
        plcy_nos = set()
        for key in POLICY_LIST_KEYS:
            for policy in result.get(key, []):
                plcy_no = policy.get("plcyNo")
                if plcy_no is not None:
                    plcy_nos.add(str(plcy_no))

        plcyno_to_policy_id = await PolicyCrud.get_policy_ids_by_plcyno(db, list(plcy_nos))

        for key in POLICY_LIST_KEYS:
            for policy in result.get(key, []):
                policy["policy_id"] = plcyno_to_policy_id.get(str(policy.get("plcyNo")))

        return result

    @staticmethod
    async def _attach_bookmark_flags(db: AsyncSession, user_id: int, result: dict) -> dict:
        """policy_id(backend DB PK) 기준으로 즐겨찾기 여부를 붙입니다. plcyNo는 사용하지 않습니다."""
        bookmarks = await BookmarkCrud.get_by_user(db, user_id)
        bookmarked_ids = {str(b.policy_id) for b in bookmarks}

        for key in POLICY_LIST_KEYS:
            for policy in result.get(key, []):
                policy["is_bookmarked"] = str(policy.get("policy_id")) in bookmarked_ids

        return result
