from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.services.recommendation.recommendation_service import RecommendationService
from app.services.recommendation.scenario_resolver import ScenarioResolver
from app.services.recommendation.schemas import ScenarioResolveRequest, ScenarioResolveResponse, UserProfileIn

router = APIRouter(prefix="/recommendations", tags=["Recommendation"])


def get_recommendation_service(request: Request) -> RecommendationService:
    return request.app.state.recommendation_service


def get_scenario_resolver(request: Request) -> ScenarioResolver:
    return request.app.state.scenario_resolver


class RecommendationRequest(BaseModel):
    user_profile: UserProfileIn


class ChatRecommendationRequest(BaseModel):
    user_profile: UserProfileIn
    chat: str


# C 맞춤형 정책 추천 (rule engine 실행, 정책 데이터는 서버에서 직접 로드)
@router.post("/")
async def recommend(data: RecommendationRequest, request: Request):
    recommendation_service = get_recommendation_service(request)
    return recommendation_service.recommend_svc(data.user_profile.model_dump(mode="json"))


# C 채팅 기반 맞춤형 정책 추천 (rule engine 통과 정책 중 유사도 top_k)
@router.post("/chat")
async def recommend_chat(data: ChatRecommendationRequest, request: Request):
    recommendation_service = get_recommendation_service(request)
    return recommendation_service.recommend_chat_svc(data.user_profile.model_dump(mode="json"), data.chat)


# C 구조화 질문(Q1 지역이동/Q2 취업 변화) 답변을 profile diff로 변환 (DB/Watson 미사용)
@router.post("/resolve-scenario", response_model=ScenarioResolveResponse)
async def resolve_scenario(data: ScenarioResolveRequest, request: Request):
    scenario_resolver = get_scenario_resolver(request)
    diff, ambiguous, notes = scenario_resolver.resolve(
        data.region_choice, data.region_text, data.employment_choice, data.employment_other
    )
    return ScenarioResolveResponse(diff=diff, ambiguous=ambiguous, notes=notes)
