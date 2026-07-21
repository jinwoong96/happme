from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.services.recommendation.income_eligibility import IncomeEligibilityService
from app.services.recommendation.recommendation_service import RecommendationService
from app.services.recommendation.scenario_resolver import ScenarioResolver
from app.services.recommendation.schemas import (
    IncomeEligibilityRequest,
    IncomeEligibilityResponse,
    ScenarioResolveRequest,
    ScenarioResolveResponse,
    UserProfileIn,
)

router = APIRouter(prefix="/recommendations", tags=["Recommendation"])


def get_recommendation_service(request: Request) -> RecommendationService:
    return request.app.state.recommendation_service


def get_scenario_resolver(request: Request) -> ScenarioResolver:
    return request.app.state.scenario_resolver


def get_income_eligibility_service(request: Request) -> IncomeEligibilityService:
    return request.app.state.income_eligibility_service


class RecommendationRequest(BaseModel):
    user_profile: UserProfileIn


class ChatRecommendationRequest(BaseModel):
    user_profile: UserProfileIn
    chat: str


class EligibilityBatchRequest(BaseModel):
    user_profile: UserProfileIn
    plcyNos: list[str]


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


# C 이미 매칭된 정책들(plcyNo 목록)에 대해서만 지원 가능 여부를 판정 (OCR/사진분석용, rule engine만 사용)
@router.post("/eligibility-batch")
async def check_eligibility_batch(data: EligibilityBatchRequest, request: Request):
    recommendation_service = get_recommendation_service(request)
    return recommendation_service.check_eligibility_svc(data.user_profile.model_dump(mode="json"), data.plcyNos)


# C 구조화 질문(Q1 지역이동/Q2 취업 변화) 답변을 profile diff로 변환 (DB/Watson 미사용)
@router.post("/resolve-scenario", response_model=ScenarioResolveResponse)
async def resolve_scenario(data: ScenarioResolveRequest, request: Request):
    scenario_resolver = get_scenario_resolver(request)
    diff, ambiguous, notes = scenario_resolver.resolve(
        data.region_choice, data.region_text, data.employment_choice, data.employment_other
    )
    return ScenarioResolveResponse(diff=diff, ambiguous=ambiguous, notes=notes)


# C 정책별 소득 조건 지원 가능 여부 판정 (rule engine 우선, 애매하면 watsonx LLM)
@router.post("/income-eligibility", response_model=IncomeEligibilityResponse)
async def judge_income_eligibility(data: IncomeEligibilityRequest, request: Request):
    income_eligibility_service = get_income_eligibility_service(request)
    result = income_eligibility_service.judge_svc(data.plcyNo, data.answers)
    return IncomeEligibilityResponse(**result)
