from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.db.crud.user_profile import UserProfileCrud
from app.db.crud.bookmark import BookmarkCrud
from app.db.scheme.user_profile import UserProfileRead
from app.services.ai_client import AiClient

POLICY_LIST_KEYS = ("available_policies", "unavailable_policies")


class RecommendationService:

    @staticmethod
    async def get_recommendations_svc(db: AsyncSession, user_id: int) -> dict:
        user_profile_payload = await RecommendationService._get_user_profile_payload(db, user_id)

        # TODO(1차 테스트 이후): 추천 결과 DB 저장, updated_at 비교를 통한 캐시 재사용 로직 추가
        result = await AiClient.recommend(user_profile_payload)
        return await RecommendationService._attach_bookmark_flags(db, user_id, result)

    @staticmethod
    async def get_chat_recommendations_svc(db: AsyncSession, user_id: int, chat: str) -> dict:
        user_profile_payload = await RecommendationService._get_user_profile_payload(db, user_id)
        result = await AiClient.recommend_chat(user_profile_payload, chat)
        return await RecommendationService._attach_bookmark_flags(db, user_id, result)

    @staticmethod
    async def _get_user_profile_payload(db: AsyncSession, user_id: int) -> dict:
        profile = await UserProfileCrud.get_profile(db, user_id)
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="프로필을 먼저 등록해주세요.")
        return UserProfileRead.model_validate(profile).model_dump(mode="json")

    @staticmethod
    async def _attach_bookmark_flags(db: AsyncSession, user_id: int, result: dict) -> dict:
        bookmarks = await BookmarkCrud.get_by_user(db, user_id)
        bookmarked_ids = {str(b.policy_id) for b in bookmarks}

        for key in POLICY_LIST_KEYS:
            for policy in result.get(key, []):
                policy["is_bookmarked"] = str(policy.get("policy_id")) in bookmarked_ids

        return result
