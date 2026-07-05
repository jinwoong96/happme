from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.db.models.user import User
from app.services.recommendation import RecommendationService as recommendation_svc
from app.core.jwt_handle import get_current_user

router = APIRouter(prefix="/recommendations", tags=["Recommendation"])


# C 맞춤형 정책 추천
@router.post("/")
async def get_recommendations(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await recommendation_svc.get_recommendations_svc(db, current_user.user_id)
    print("백엔드 서버 추천 응답")
    print(result)
    return result
