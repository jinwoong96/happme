from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app.services.recommendation.similarity_search import PolicySimilarityService

router = APIRouter(prefix="/policy-dedup", tags=["PolicyDedup"])


def get_policy_similarity_service(request: Request) -> PolicySimilarityService:
    return request.app.state.policy_similarity_service


class DedupSearchRequest(BaseModel):
    query_text: str
    top_k: int = Field(5, ge=1, le=20)


class DedupMatch(BaseModel):
    plcyNo: str | None = None
    policy_name: str | None = None
    policy_summary: str | None = None
    score: float


# 관리자 공고문 등록/수정 화면의 중복(유사) 정책 탐지. BAAI/bge-m3 임베딩 코퍼스 전체를 대상으로 검색한다.
@router.post("/search", response_model=list[DedupMatch])
async def search_similar_policies(data: DedupSearchRequest, request: Request):
    service = get_policy_similarity_service(request)
    return service.search_all(data.query_text, top_k=data.top_k)
