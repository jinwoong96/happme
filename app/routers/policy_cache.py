from typing import Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter(prefix="/policy-cache", tags=["PolicyCache"])


def get_policy_loader(request: Request):
    """앱 시작 시 만들어 둔 PolicyLoaderService(메모리 캐시) 인스턴스를 꺼내온다."""
    return request.app.state.policy_loader


def get_rule_engine_cache(request: Request):
    return request.app.state.rule_engine_cache


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
# 정책 내용이 바뀌면 RuleEngineCache의 변경 로그에 이 plcyNo를 남긴다 - persona 캐시를 통째로
# 지우거나 그 자리에서 모든 persona를 재계산하지 않고, 각 persona가 다음에 조회될 때 이
# plcyNo만 그 persona 기준으로 다시 평가해서 갱신한다(recommendation_service.py의
# _get_persona_matches 참고).
@router.post("/upsert")
async def upsert_policy_cache(data: PolicyCacheUpsert, request: Request):
    policy_loader = get_policy_loader(request)
    policy_loader.upsert_policy(data.model_dump())
    if data.plcyNo:
        get_rule_engine_cache(request).mark_policy_changed(data.plcyNo)
    return {"message": "ok"}


# D 정책 삭제 시 메모리 캐시에서도 제거.
@router.delete("/{policy_id}")
async def remove_policy_cache(policy_id: int, request: Request):
    policy_loader = get_policy_loader(request)
    removed_plcyno = policy_loader.remove_policy(policy_id)
    if removed_plcyno:
        get_rule_engine_cache(request).mark_policy_changed(removed_plcyno)
    return {"message": "ok"}


# rule engine 캐시 전체를 수동으로 비운다. 평소엔 upsert/delete 시 변경 로그에 plcyNo만 남기고
# 각 persona가 다음 조회될 때 그 변경분만 반영하지만, eligibility_rules.py의 판정 로직 자체가
# 바뀌었을 때는(정책 데이터는 안 바뀌어도) 기존 persona 캐시가 옛 로직 기준 결과를 계속 들고
# 있으므로 통째로 비워야 한다. 서버 재시작 없이 필요할 때 Swagger UI에서 수동 호출하는 용도.
@router.post("/rule-engine-cache/clear")
async def clear_rule_engine_cache(request: Request):
    cache = get_rule_engine_cache(request)
    before = cache.stats()
    cache.clear()
    return {"message": "ok", "cleared": before}
