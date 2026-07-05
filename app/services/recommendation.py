from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.db.crud.user_profile import UserProfileCrud
from app.db.scheme.user_profile import UserProfileRead
from app.services.ai_client import AiClient


class RecommendationService:

    @staticmethod
    async def get_recommendations_svc(db: AsyncSession, user_id: int) -> dict:
        profile = await UserProfileCrud.get_profile(db, user_id)
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="프로필을 먼저 등록해주세요.")

        user_profile_payload = UserProfileRead.model_validate(profile).model_dump(mode="json")

        # TODO(1차 테스트 이후): 추천 결과 DB 저장, updated_at 비교를 통한 캐시 재사용 로직 추가
        return await AiClient.recommend(user_profile_payload)
