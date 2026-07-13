from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.db.models.user import User
from app.db.scheme.recommendation import ChatRecommendationRequest, IncomeEligibilityRequest, ScenarioRecommendationRequest
from app.services.recommendation import RecommendationService as recommendation_svc
from app.core.jwt_handle import get_current_user

router = APIRouter(prefix="/recommendations", tags=["Recommendation"])


# C 맞춤형 정책 추천
@router.post("/")
async def get_recommendations(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await recommendation_svc.get_recommendations_svc(db, current_user.user_id)


# C 채팅 기반 맞춤형 정책 추천
@router.post("/chat")
async def get_chat_recommendations(
    data: ChatRecommendationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await recommendation_svc.get_chat_recommendations_svc(db, current_user.user_id, data.chat)


# C 구조화 질문(Q1 지역이동/Q2 취업 변화/Q3 상황) 기반 what-if 시뮬레이션 추천
@router.post("/scenario")
async def get_scenario_recommendations(
    data: ScenarioRecommendationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await recommendation_svc.get_scenario_recommendations_svc(db, current_user.user_id, data)


# C 정책 카드의 "소득계산" 버튼: 모달 답변으로 소득 조건 충족 여부 판정 (답변은 저장하지 않음)
@router.post("/income-eligibility")
async def get_income_eligibility(data: IncomeEligibilityRequest, current_user: User = Depends(get_current_user)):
    return await recommendation_svc.judge_income_eligibility_svc(data.plcyNo, data.answers)
