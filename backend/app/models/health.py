import enum
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Enum, ForeignKey, Text, Integer, Float
from app.db.types import GUID
from sqlalchemy.orm import relationship
from app.db.session import Base


class QueryLanguage(str, enum.Enum):
    en = "en"
    hi = "hi"
    or_ = "or"


class HealthQuery(Base):
    """A citizen's question to the AI assistant, plus the safe response given."""
    __tablename__ = "health_queries"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=True)  # null if anonymous
    session_id = Column(String(64), nullable=False, index=True)
    question_text = Column(Text, nullable=False)
    language = Column(Enum(QueryLanguage), default=QueryLanguage.en)
    ai_response_text = Column(Text, nullable=True)
    sources = Column(Text, nullable=True)  # JSON-encoded list of source citations
    safety_flag = Column(String(50), nullable=True)  # e.g. 'emergency', 'self_harm', 'ok'
    ai_provider = Column(String(20), default="demo")  # 'gemini' or 'demo'
    detected_symptom_tags = Column(Text, nullable=True)  # JSON-encoded list
    intent = Column(String(50), nullable=True)  # see services/intent.py Intent enum
    topic_category = Column(String(50), nullable=True)  # see services/taxonomy.py HealthCategory
    topic_tag = Column(String(100), nullable=True)  # specific disease/topic if named, else null
    contributed_to_public_health = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="queries")


class AnonymizedSymptomReport(Base):
    """
    De-identified, k-anonymized record derived from a HealthQuery after user consent.
    No direct or quasi-identifiers linking back to the user are stored here.
    """
    __tablename__ = "anonymized_symptom_reports"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    symptom_tag = Column(String(100), nullable=False, index=True)
    district_bucket = Column(String(100), nullable=False, index=True)  # generalized region, not exact address
    age_bucket = Column(String(20), nullable=True)  # e.g. '18-30' — generalized, optional
    week_bucket = Column(String(10), nullable=False, index=True)  # ISO week, e.g. '2026-W32'
    created_at = Column(DateTime, default=datetime.utcnow)


class EarlyAwarenessSignal(Base):
    """
    Output of the Early Awareness Engine: a statistical anomaly in aggregated,
    anonymized symptom trends. This is NOT a confirmed outbreak — it requires
    human/public-health review before any action is taken.
    """
    __tablename__ = "early_awareness_signals"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    symptom_tag = Column(String(100), nullable=False)
    district_bucket = Column(String(100), nullable=False)
    week_bucket = Column(String(10), nullable=False)
    observed_count = Column(Integer, nullable=False)
    baseline_mean = Column(Float, nullable=False)
    baseline_stddev = Column(Float, nullable=False)
    z_score = Column(Float, nullable=False)
    severity = Column(String(20), nullable=False)  # 'low', 'moderate', 'high'
    status = Column(String(20), default="pending_review")  # pending_review, acknowledged, dismissed
    reviewed_by = Column(GUID(), ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
