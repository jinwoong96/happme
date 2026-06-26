from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class PolicyCreate(BaseModel):
    plcyNo: Optional[str] = None
    plcyNm: str
    plcyKywdNm: str
    plcyExplnCn: str
    lclsfNm: str
    mclsfNm: str
    plcySprtCn: str
    sprvsnInstCdNm: Optional[str] = None
    sprvsnInstPicNm: Optional[str] = None
    operInstCdNm: Optional[str] = None
    operInstPicNm: Optional[str] = None
    bizPrdBgngYmd: Optional[str] = None
    bizPrdEndYmd: Optional[str] = None
    bizPrdEtcCn: Optional[str] = None
    plcyAplyMthdCn: Optional[str] = None
    aplyUrlAddr: Optional[str] = None
    sbmsnDcmntCn: str
    aplyYmd: str
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
    sprvsnInstCdNm: Optional[str] = None
    sprvsnInstPicNm: Optional[str] = None
    operInstCdNm: Optional[str] = None
    operInstPicNm: Optional[str] = None
    bizPrdBgngYmd: Optional[str] = None
    bizPrdEndYmd: Optional[str] = None
    bizPrdEtcCn: Optional[str] = None
    plcyAplyMthdCn: Optional[str] = None
    aplyUrlAddr: Optional[str] = None
    sbmsnDcmntCn: Optional[str] = None
    aplyYmd: Optional[str] = None
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
    sprvsnInstCdNm: Optional[str] = None
    sprvsnInstPicNm: Optional[str] = None
    operInstCdNm: Optional[str] = None
    operInstPicNm: Optional[str] = None
    bizPrdBgngYmd: Optional[str] = None
    bizPrdEndYmd: Optional[str] = None
    bizPrdEtcCn: Optional[str] = None
    plcyAplyMthdCn: Optional[str] = None
    aplyUrlAddr: Optional[str] = None
    sbmsnDcmntCn: str
    aplyYmd: str
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
    frstRegDt: Optional[datetime] = None
    lastMdfcnDt: Optional[datetime] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
    regions: List[PolicyRegionRead] = []

    class Config:
        from_attributes = True


class PolicyListRead(BaseModel):
    policy_id: int
    plcyNm: str
    plcyKywdNm: str
    lclsfNm: str
    mclsfNm: str
    sprtTrgtMinAge: int
    sprtTrgtMaxAge: int
    aplyYmd: str
    inqCnt: int
    createdAt: Optional[datetime] = None

    class Config:
        from_attributes = True
