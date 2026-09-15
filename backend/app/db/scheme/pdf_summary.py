from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class PdfSummaryMatchRead(BaseModel):
    policy_id: int
    match_score: Optional[float] = None
    match_type: Optional[str] = None

    class Config:
        from_attributes = True


class PdfSummaryCreate(BaseModel):
    user_id: int
    summary_text: str


class PdfSummaryRead(BaseModel):
    pdf_id: int
    user_id: int
    summary_text: str
    created_at: Optional[datetime] = None
    matches: List[PdfSummaryMatchRead] = []

    class Config:
        from_attributes = True


class PdfMatchCreate(BaseModel):
    pdf_id: int
    policy_id: int
    match_score: Optional[float] = None
    match_type: Optional[str] = None

class PdfAnalyzeText(BaseModel):
    text: str


class PdfAnalyzeUrl(BaseModel):
    url: str


class PdfAskQuestion(BaseModel):
    policy_name: str
    question: str