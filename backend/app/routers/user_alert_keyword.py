from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.db.scheme.user_alert_keyword import UserAlertKeywordCreate, UserAlertKeywordRead
from app.db.models.user import User
from app.services.user_alert_keyword import UserAlertKeywordService as alert_keyword_svc
from app.core.jwt_handle import get_current_user

router = APIRouter(prefix="/alert-keywords", tags=["AlertKeyword"])


# C 생성 (지원금 알림 탭 "공고문 알림 받기" 버튼 -> 텍스트 입력)
@router.post("/", response_model=UserAlertKeywordRead, status_code=201)
async def create_alert_keyword(
    data: UserAlertKeywordCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data.user_id = current_user.user_id
    return await alert_keyword_svc.create_keyword_svc(db, data)


# R 내 알림 키워드 목록
@router.get("/me", response_model=list[UserAlertKeywordRead])
async def get_my_alert_keywords(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await alert_keyword_svc.get_keywords_svc(db, current_user.user_id)


# D 삭제
@router.delete("/{keyword_id}")
async def delete_alert_keyword(
    keyword_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await alert_keyword_svc.delete_keyword_svc(db, keyword_id, current_user.user_id)
