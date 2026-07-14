from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, List


class PolicyCreate(BaseModel):
    plcyNo: Optional[str] = None
    plcyNm: str
    plcyKywdNm: str
    plcyExplnCn: str
    lclsfNm: str
    mclsfNm: str
    plcySprtCn: str
    rgtrInstCdNm: Optional[str] = None
    maxSprtAmt: Optional[int] = None
    sprvsnInstCdNm: Optional[str] = None
    sprvsnInstPicNm: Optional[str] = None
    operInstCdNm: Optional[str] = None
    operInstPicNm: Optional[str] = None
    bizPrdBgngYmd: Optional[str] = None
    bizPrdEndYmd: Optional[str] = None
    bizPrdEtcCn: Optional[str] = None
    plcyAplyMthdCn: Optional[str] = None
    srngMthdCn: Optional[str] = None
    aplyUrlAddr: Optional[str] = None
    sbmsnDcmntCn: str
    aplyYmd: str
    aplyEndDt: Optional[date] = None
    refUrlAddr1: Optional[str] = None
    refUrlAddr2: Optional[str] = None
    etcMttrCn: Optional[str] = None
    sprtSclCnt: Optional[int] = None
    sprtTrgtMinAge: int
    sprtTrgtMaxAge: int
    earnMinAmt: Optional[int] = None
    earnMaxAmt: Optional[int] = None
    earnEtcCn: str
    earnCndSeCd: Optional[str] = None
    addAplyQlfcCndCn: str
    ptcpPrpTrgtCn: str
    mrgSttsCd: Optional[str] = None
    frstRegDt: Optional[datetime] = None
    lastMdfcnDt: Optional[datetime] = None


class PolicyUpdate(BaseModel):
    plcyNm: Optional[str] = None
    plcyKywdNm: Optional[str] = None
    plcyExplnCn: Optional[str] = None
    lclsfNm: Optional[str] = None
    mclsfNm: Optional[str] = None
    plcySprtCn: Optional[str] = None
    rgtrInstCdNm: Optional[str] = None
    maxSprtAmt: Optional[int] = None
    sprvsnInstCdNm: Optional[str] = None
    sprvsnInstPicNm: Optional[str] = None
    operInstCdNm: Optional[str] = None
    operInstPicNm: Optional[str] = None
    bizPrdBgngYmd: Optional[str] = None
    bizPrdEndYmd: Optional[str] = None
    bizPrdEtcCn: Optional[str] = None
    plcyAplyMthdCn: Optional[str] = None
    srngMthdCn: Optional[str] = None
    aplyUrlAddr: Optional[str] = None
    sbmsnDcmntCn: Optional[str] = None
    aplyYmd: Optional[str] = None
    aplyEndDt: Optional[date] = None
    refUrlAddr1: Optional[str] = None
    refUrlAddr2: Optional[str] = None
    etcMttrCn: Optional[str] = None
    sprtSclCnt: Optional[int] = None
    sprtTrgtMinAge: Optional[int] = None
    sprtTrgtMaxAge: Optional[int] = None
    earnMinAmt: Optional[int] = None
    earnMaxAmt: Optional[int] = None
    earnEtcCn: Optional[str] = None
    earnCndSeCd: Optional[str] = None
    addAplyQlfcCndCn: Optional[str] = None
    ptcpPrpTrgtCn: Optional[str] = None
    mrgSttsCd: Optional[str] = None
    frstRegDt: Optional[datetime] = None
    lastMdfcnDt: Optional[datetime] = None


class PolicyRegionRead(BaseModel):
    zip_code: str

    class Config:
        from_attributes = True


class PolicyRead(BaseModel):
    policy_id: int
    plcyNo: Optional[str] = None
    plcyNm: str
    plcyKywdNm: str
    plcyExplnCn: str
    lclsfNm: str
    mclsfNm: str
    plcySprtCn: str
    rgtrInstCdNm: Optional[str] = None
    maxSprtAmt: Optional[int] = None
    sprvsnInstCdNm: Optional[str] = None
    sprvsnInstPicNm: Optional[str] = None
    operInstCdNm: Optional[str] = None
    operInstPicNm: Optional[str] = None
    bizPrdBgngYmd: Optional[str] = None
    bizPrdEndYmd: Optional[str] = None
    bizPrdEtcCn: Optional[str] = None
    plcyAplyMthdCn: Optional[str] = None
    srngMthdCn: Optional[str] = None
    aplyUrlAddr: Optional[str] = None
    sbmsnDcmntCn: str
    aplyYmd: str
    aplyEndDt: Optional[date] = None
    refUrlAddr1: Optional[str] = None
    refUrlAddr2: Optional[str] = None
    etcMttrCn: Optional[str] = None
    sprtSclCnt: Optional[int] = None
    sprtTrgtMinAge: int
    sprtTrgtMaxAge: int
    earnMinAmt: Optional[int] = None
    earnMaxAmt: Optional[int] = None
    earnEtcCn: str
    earnCndSeCd: Optional[str] = None
    addAplyQlfcCndCn: str
    ptcpPrpTrgtCn: str
    mrgSttsCd: Optional[str] = None
    inqCnt: int
    bookmarkCnt: int
    frstRegDt: Optional[datetime] = None
    lastMdfcnDt: Optional[datetime] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
    regions: List[PolicyRegionRead] = []

    # 카드 표시용(policy_cards.json 기반). 매칭되는 카드가 없으면 None.
    policy_summary: Optional[str] = None
    apply_period_type: Optional[str] = None
    apply_period: Optional[str] = None
    target: Optional[str] = None

    class Config:
        from_attributes = True


class PolicySimilaritySearchRequest(BaseModel):
    query_text: str
    top_k: int = 5


class PolicySimilarityMatch(BaseModel):
    policy: PolicyRead
    score: float

    class Config:
        from_attributes = True


class PolicyListRead(BaseModel):
    policy_id: int
    plcyNo: Optional[str] = None
    plcyNm: str
    plcyKywdNm: str
    lclsfNm: str
    mclsfNm: str
    rgtrInstCdNm: Optional[str] = None
    sprtTrgtMinAge: int
    sprtTrgtMaxAge: int
    aplyYmd: str
    aplyEndDt: Optional[date] = None
    inqCnt: int
    bookmarkCnt: int
    maxSprtAmt: Optional[int] = None
    createdAt: Optional[datetime] = None

    # 카드 표시용(policy_cards.json 기반). 매칭되는 카드가 없으면 None.
    policy_summary: Optional[str] = None
    apply_period_type: Optional[str] = None
    apply_period: Optional[str] = None
    target: Optional[str] = None

    # 홈 화면 배너 전용. amount(지원금액 높은 순)/deadline(마감임박)/latest(최신 등록) 중 하나.
    banner_reason: Optional[str] = None

    class Config:
        from_attributes = True
