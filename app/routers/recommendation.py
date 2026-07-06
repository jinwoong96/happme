from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.db.models.user import User
from app.db.scheme.recommendation import ChatRecommendationRequest
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
