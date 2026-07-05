from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.services.recommendation.recommendation_service import RecommendationService
from app.services.recommendation.schemas import UserProfileIn

router = APIRouter(prefix="/recommendations", tags=["Recommendation"])


def get_recommendation_service(request: Request) -> RecommendationService:
    return request.app.state.recommendation_service


class RecommendationRequest(BaseModel):
    user_profile: UserProfileIn


# C 맞춤형 정책 추천 (rule engine 실행, 정책 데이터는 서버에서 직접 로드)
@router.post("/")
async def recommend(data: RecommendationRequest, request: Request):
    recommendation_service = get_recommendation_service(request)
    return recommendation_service.recommend_svc(data.user_profile.model_dump(mode="json"))
