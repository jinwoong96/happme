from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class OcrResultMatchRead(BaseModel):
    policy_id: int
    match_score: Optional[float] = None
    match_type: Optional[str] = None

    class Config:
        from_attributes = True


class OcrResultCreate(BaseModel):
    user_id: int
    extracted_text: str


class OcrResultRead(BaseModel):
    ocr_id: int
    user_id: int
    extracted_text: str
    created_at: Optional[datetime] = None
    matches: List[OcrResultMatchRead] = []

    class Config:
        from_attributes = True


class OcrMatchCreate(BaseModel):
    ocr_id: int
    policy_id: int
    match_score: Optional[float] = None
    match_type: Optional[str] = None
