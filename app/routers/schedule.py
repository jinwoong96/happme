from typing import Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.services.schedule_extract import ScheduleService

router = APIRouter(prefix="/schedule", tags=["Schedule"])


class ScheduleExtractRequest(BaseModel):
    plcyNm: str = ""
    plcyExplnCn: str = ""
    plcyAplyMthdCn: str = ""
    srngMthdCn: str = ""
    aplyYmd: str = ""
    frstRegDt: str = ""


class ScheduleEvent(BaseModel):
    type: str
    date: str
    raw_text: str


class ScheduleExtractResponse(BaseModel):
    events: list[ScheduleEvent]
    prep_tip: Optional[str] = None


def get_schedule_service(request: Request) -> ScheduleService:
    return request.app.state.schedule_service


# C 정책 공고문에서 일정 추출 + 준비 팁 생성
@router.post("/extract", response_model=ScheduleExtractResponse)
async def extract_schedule(data: ScheduleExtractRequest, request: Request):
    schedule_service = get_schedule_service(request)
    policy = data.model_dump()

    events = schedule_service.extract_events_svc(policy)
    prep_tip = schedule_service.generate_prep_tip_svc(policy, events)

    return ScheduleExtractResponse(events=events, prep_tip=prep_tip)


# R 헬스체크
@router.get("/health")
async def health_check(request: Request):
    schedule_service = get_schedule_service(request)
    return {"status": "ok", "enabled": schedule_service.enabled}
