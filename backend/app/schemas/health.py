import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class QueryRequest(BaseModel):
    question: str
    session_id: str
    language: str = "en"


class SourceOut(BaseModel):
    title: str
    source_name: str
    source_url: Optional[str] = None
    snippet: str


class QueryResponse(BaseModel):
    query_id: uuid.UUID
    answer: str
    sources: List[SourceOut]
    provider: str
    safety_flag: str
    detected_symptom_tags: List[str]


class ConsentRequest(BaseModel):
    query_id: uuid.UUID
    granted: bool
    age_bucket: Optional[str] = None


class AwarenessSignalOut(BaseModel):
    id: uuid.UUID
    symptom_tag: str
    district_bucket: str
    week_bucket: str
    observed_count: int
    baseline_mean: float
    z_score: float
    severity: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class AwarenessReviewRequest(BaseModel):
    status: str  # 'acknowledged' | 'dismissed'
    review_notes: Optional[str] = None
