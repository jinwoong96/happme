from typing import Literal, Optional

from pydantic import BaseModel


class ChatRecommendationRequest(BaseModel):
    chat: str


class ScenarioRecommendationRequest(BaseModel):
    """Q1(지역이동)/Q2(취업 변화)/Q3(상황 설명) 구조화 답변으로 시뮬레이션 추천을 요청."""

    region_choice: Literal["지역 쓰기", "지역 이동 안함", "미정"]
    region_text: Optional[str] = None
    employment_choice: Literal["이직", "퇴사", "창업", "재직", "기타"]
    employment_other: Optional[str] = None
    situation: str
