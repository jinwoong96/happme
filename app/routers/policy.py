from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.db.scheme.policy import (
    PolicyCreate, PolicyUpdate, PolicyRead, PolicyListRead,
    PolicySimilaritySearchRequest, PolicySimilarityMatch,
)
from app.services.policy import PolicyService as policy_svc
from app.db.models.user import User
from app.core.admin import get_current_admin

router = APIRouter(prefix="/policies", tags=["Policy"])


# C 생성 (관리자용)
@router.post("/", response_model=PolicyRead, status_code=201)
async def create_policy(data: PolicyCreate, db: AsyncSession = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    return await policy_svc.create_policy_svc(db, data)


# 유사(중복 의심) 공고문 검색 (관리자용, BAAI/bge-m3 임베딩)
@router.post("/similarity-search", response_model=list[PolicySimilarityMatch])
async def search_similar_policies(
    data: PolicySimilaritySearchRequest,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    return await policy_svc.similarity_search_svc(db, data.query_text, top_k=data.top_k)


# R 전체 조회 (필터링)
@router.get("/", response_model=list[PolicyListRead])
async def get_all_policies(
    age: Optional[int] = Query(None, description="나이 필터"),
    region: Optional[str] = Query(None, description="지역 코드 (우편번호 prefix)"),
    lclsf: Optional[str] = Query(None, description="대분류명"),
    keyword: Optional[str] = Query(None, description="검색 키워드"),
    sort: Optional[str] = Query(None, description="정렬 기준: latest(최신 등록순), popular(인기순), alpha(가나다순), deadline(마감임박순). 생략 시 정렬 없음"),
    include_closed: bool = Query(False, description="마감된 정책 포함 여부 (기본: 마감 지난 정책 제외)"),
    consonant: Optional[str] = Query(None, description="가나다순 초성 필터: ㄱ~ㅎ, 기타. 생략 시 전체"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    return await policy_svc.get_all_policies_svc(
        db, age=age, region=region, lclsf=lclsf, keyword=keyword, sort=sort, include_closed=include_closed,
        consonant=consonant, limit=limit, offset=offset,
    )


# 홈 화면 "이번 달 정책 추천" 배너 (지원금액 높은 순/마감임박/최신 등록 순으로 중복 없이 구성).
# "/{policy_id}"보다 먼저 선언해야 "home-banner"가 int 파싱 대상으로 잘못 매칭되지 않는다.
@router.get("/home-banner", response_model=list[PolicyListRead])
async def get_home_banner(db: AsyncSession = Depends(get_db)):
    return await policy_svc.get_home_banner_svc(db)


# R 단일 조회
@router.get("/{policy_id}", response_model=PolicyRead)
async def get_policy(policy_id: int, db: AsyncSession = Depends(get_db)):
    return await policy_svc.get_policy_svc(db, policy_id)


# U 수정 (관리자용)
@router.patch("/{policy_id}", response_model=PolicyRead)
async def update_policy(policy_id: int, data: PolicyUpdate, db: AsyncSession = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    return await policy_svc.update_policy_svc(db, policy_id, data)


# D 삭제 (관리자용)
@router.delete("/{policy_id}")
async def delete_policy(policy_id: int, db: AsyncSession = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    return await policy_svc.delete_policy_svc(db, policy_id)


# 지역 추가 (관리자용)
@router.post("/{policy_id}/regions")
async def add_region(policy_id: int, zip_code: str = Query(...), db: AsyncSession = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    return await policy_svc.add_region_svc(db, policy_id, zip_code)
