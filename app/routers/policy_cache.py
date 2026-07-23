from typing import Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter(prefix="/policy-cache", tags=["PolicyCache"])


def get_policy_loader(request: Request):
    """앱 시작 시 만들어 둔 PolicyLoaderService(메모리 캐시) 인스턴스를 꺼내온다."""
    return request.app.state.policy_loader


class PolicyCacheUpsert(BaseModel):
    """PolicyLoaderService.FIELDS + zipCd. bene_backend가 정책 생성/수정 직후, 또는
    외부 동기화(최신화) 배치가 끝난 뒤 신규/변경된 정책마다 이 스키마로 보내준다."""
    policy_id: int
    plcyNo: Optional[str] = None
    plcyNm: Optional[str] = None
    plcyExplnCn: Optional[str] = None
    plcySprtCn: Optional[str] = None
    plcyKywdNm: Optional[str] = None
    lclsfNm: Optional[str] = None
    mclsfNm: Optional[str] = None
    rgtrInstCdNm: Optional[str] = None
    aplyPrdSeCd: Optional[str] = None
    aplyYmd: Optional[str] = None
    sprtTrgtAgeLmtYn: Optional[str] = None
    sprtTrgtMinAge: Optional[int] = None
    sprtTrgtMaxAge: Optional[int] = None
    mrgSttsCd: Optional[str] = None
    schoolCd: Optional[str] = None
    plcyMajorCd: Optional[str] = None
    sbizCd: Optional[str] = None
    jobCd: Optional[str] = None
    earnCndSeCd: Optional[str] = None
    earnEtcCn: Optional[str] = None
    earnMinAmt: Optional[int] = None
    earnMaxAmt: Optional[int] = None
    zipCd: Optional[str] = None


# C/U 정책 1건을 메모리 캐시(PolicyLoaderService)에 즉시 반영 (재시작 없이).
# PolicyLoaderService는 서버 시작 시 DB를 한 번만 읽어 캐싱하므로, 이 엔드포인트 없이는
# 서버가 뜬 이후 생성/수정된 정책이 추천/알림 매칭에 영원히 안 잡힌다.
@router.post("/upsert")
async def upsert_policy_cache(data: PolicyCacheUpsert, request: Request):
    policy_loader = get_policy_loader(request)
    policy_loader.upsert_policy(data.model_dump())
    return {"message": "ok"}


# D 정책 삭제 시 메모리 캐시에서도 제거.
@router.delete("/{policy_id}")
async def remove_policy_cache(policy_id: int, request: Request):
    policy_loader = get_policy_loader(request)
    policy_loader.remove_policy(policy_id)
    return {"message": "ok"}
