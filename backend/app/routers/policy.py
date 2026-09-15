from typing import Optional
from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.db.scheme.policy import (
    PolicyCreate, PolicyUpdate, PolicyRead, PolicyListRead,
    PolicySimilaritySearchRequest, PolicySimilarityMatch, PolicyCompareRequest,
)
from app.services.policy import PolicyService as policy_svc
from app.services import external_sync
from app.services.ai_client import AiClient
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
    mclsf: Optional[str] = Query(None, description="중분류명"),
    keyword: Optional[str] = Query(None, description="검색 키워드"),
    sort: Optional[str] = Query(None, description="정렬 기준: latest(최신 등록순), popular(인기순), alpha(가나다순), deadline(마감임박순). 생략 시 정렬 없음"),
    include_closed: bool = Query(False, description="마감된 정책 포함 여부 (기본: 마감 지난 정책 제외)"),
    consonant: Optional[str] = Query(None, description="가나다순 초성 필터: ㄱ~ㅎ, 기타. 생략 시 전체"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    return await policy_svc.get_all_policies_svc(
        db, age=age, region=region, lclsf=lclsf, mclsf=mclsf, keyword=keyword, sort=sort,
        include_closed=include_closed, consonant=consonant, limit=limit, offset=offset,
    )


# 중분류(mclsfNm) 목록 (관리자 화면 카테고리 필터 드롭다운용). /{policy_id}보다 먼저 선언해야
# "categories"가 policy_id로 파싱되는 걸 막을 수 있다.
@router.get("/categories", response_model=list[str])
async def get_categories(db: AsyncSession = Depends(get_db)):
    return await policy_svc.get_category_list_svc(db)


# 홈 화면 "이번 달 정책 추천" 배너 (지원금액 높은 순/마감임박/최신 등록 순으로 중복 없이 구성).
# "/{policy_id}"보다 먼저 선언해야 "home-banner"가 int 파싱 대상으로 잘못 매칭되지 않는다.
@router.get("/home-banner", response_model=list[PolicyListRead])
async def get_home_banner(db: AsyncSession = Depends(get_db)):
    return await policy_svc.get_home_banner_svc(db)


# 외부 데이터(온통청년/복지로) 최신화 - 관리자 사이트 "최신화" 버튼용.
# 백그라운드에서 기존 import 스크립트들을 순서대로 실행한다 (수동 트리거, 자동 스케줄은 아직 없음).
@router.post("/refresh")
async def refresh_external_policies(
    background_tasks: BackgroundTasks,
    current_admin: User = Depends(get_current_admin),
):
    status = external_sync.get_status()
    if status["running"]:
        return {"message": "이미 최신화가 진행 중입니다.", "status": status}
    background_tasks.add_task(external_sync.run_refresh_all)
    return {"message": "최신화를 시작했습니다."}


@router.get("/refresh/status")
async def get_refresh_status(current_admin: User = Depends(get_current_admin)):
    return external_sync.get_status()


# 즐겨찾기 비교(AI 요약): 2~3개 policy_id를 넘기면 각각 짧은 요약 + 비교 코멘트를 반환.
# "/{policy_id}"보다 먼저 선언해야 "compare"가 int 파싱 대상으로 잘못 매칭되지 않는다.
@router.post("/compare")
async def compare_policies(data: PolicyCompareRequest, db: AsyncSession = Depends(get_db)):
    return await policy_svc.compare_policies_svc(db, data.policy_ids)


# 채팅 추천/중복탐지에 쓰는 정책 검색문서(policy_search_docs.json)를, DB에 새로 추가된 정책만
# 골라 생성해서 이어붙이는 백그라운드 작업을 bene_ai에 트리거한다 (관리자용).
# "/{policy_id}"보다 먼저 선언해야 "search-docs"가 int 파싱 대상으로 잘못 매칭되지 않는다.
@router.post("/search-docs/rebuild")
async def rebuild_search_docs(current_admin: User = Depends(get_current_admin)):
    return await AiClient.trigger_search_docs_rebuild()


@router.get("/search-docs/rebuild/status")
async def get_search_docs_rebuild_status(current_admin: User = Depends(get_current_admin)):
    return await AiClient.get_search_docs_rebuild_status()


# DB에 summary가 비어있는 정책만 골라 채우는 백그라운드 작업을 bene_ai에 트리거한다 (관리자용).
# "/{policy_id}"보다 먼저 선언해야 "policy-summary"가 int 파싱 대상으로 잘못 매칭되지 않는다.
@router.post("/policy-summary/rebuild")
async def rebuild_policy_summaries(current_admin: User = Depends(get_current_admin)):
    return await AiClient.trigger_policy_summary_rebuild()


@router.get("/policy-summary/rebuild/status")
async def get_policy_summary_rebuild_status(current_admin: User = Depends(get_current_admin)):
    return await AiClient.get_policy_summary_rebuild_status()


# 공고문 PDF/텍스트/URL 매칭용 캐시(PdfSummaryService)를 DB 최신 상태로 갱신하는 백그라운드
# 작업을 bene_ai에 트리거한다 (관리자용). "/{policy_id}"보다 먼저 선언.
@router.post("/pdf-cache/rebuild")
async def rebuild_pdf_cache(current_admin: User = Depends(get_current_admin)):
    return await AiClient.trigger_pdf_cache_rebuild()


@router.get("/pdf-cache/rebuild/status")
async def get_pdf_cache_rebuild_status(current_admin: User = Depends(get_current_admin)):
    return await AiClient.get_pdf_cache_rebuild_status()


# bene_ai의 rule engine 캐시(persona+plcyNo 단위로 자격판정 결과를 캐싱한 것) 전체를 수동으로
# 비운다. 평소엔 정책 CUD 시 정책 단위로만 무효화되지만, eligibility_rules.py의 판정 로직 자체가
# 바뀌었을 때는(정책 데이터는 안 바뀌어도) 기존 캐시가 옛 로직 기준 결과를 계속 들고 있으므로
# 전체를 비워야 한다. "/{policy_id}"보다 먼저 선언.
@router.post("/rule-engine-cache/clear")
async def clear_rule_engine_cache(current_admin: User = Depends(get_current_admin)):
    return await AiClient.clear_rule_engine_cache()


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
