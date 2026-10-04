"""
SIGNAL PLANE models.

Architectural rule: the government dashboard and Early Awareness Engine may
ONLY read from this module's tables (GeoBlock, SignalEvent, Alert). They must
NEVER query HealthQuery or User directly - that table lives in the
CONVERSATION PLANE (app/models/health.py's HealthQuery) and contains
per-citizen interaction data. See services/signals.py for the one-way
write path from conversation plane -> signal plane (only triggered by
explicit consent).
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, Float, ForeignKey, Text
from app.db.types import GUID
from app.db.session import Base


class GeoBlock(Base):
    """
    Coarse geography unit. Signals are aggregated at this level, never at
    exact GPS. latitude/longitude are the BLOCK CENTROID (a deliberately
    coarse approximation, e.g. town/block-center) - never derived from any
    individual citizen's location, consistent with the privacy model.
    """
    __tablename__ = "geo_blocks"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    block_name = Column(String(100), nullable=False)
    district = Column(String(100), nullable=False, index=True)
    state = Column(String(100), nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)


class SignalEvent(Base):
    """
    A single aggregated count of consented, anonymized health-topic
    mentions for one (topic_category, geo_block, day) combination.
    Contains NO identifying information whatsoever - no user_id, no raw
    question text, no session id, no exact location.
    """
    __tablename__ = "signal_events"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    topic_category = Column(String(50), nullable=False, index=True)  # HealthCategory value
    topic_tag = Column(String(100), nullable=True)  # specific disease if known, else null
    geo_block_id = Column(GUID(), ForeignKey("geo_blocks.id"), nullable=False, index=True)
    day_bucket = Column(String(10), nullable=False, index=True)  # ISO date, e.g. '2026-08-11'
    count = Column(Integer, nullable=False, default=1)
    is_simulated = Column(Integer, default=0)  # 1 = demo/simulated data, must be labeled as such in UI
    created_at = Column(DateTime, default=datetime.utcnow)


class Alert(Base):
    """
    Output of the Early Awareness Engine: a statistical anomaly, NOT a
    confirmed outbreak. Every alert starts status='pending_review' and
    requires a human health_official to acknowledge or dismiss it.
    """
    __tablename__ = "alerts"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    topic_category = Column(String(50), nullable=False)
    topic_tag = Column(String(100), nullable=True)
    geo_block_id = Column(GUID(), ForeignKey("geo_blocks.id"), nullable=False)
    period_bucket = Column(String(10), nullable=False)  # day or week bucket the anomaly was detected in
    observed_count = Column(Integer, nullable=False)
    baseline_mean = Column(Float, nullable=False)
    baseline_stddev = Column(Float, nullable=False)
    z_score = Column(Float, nullable=False)
    severity = Column(String(20), nullable=False)  # low, moderate, high
    status = Column(String(20), default="pending_review")  # pending_review, acknowledged, dismissed
    is_simulated = Column(Integer, default=0)
    generated_at = Column(DateTime, default=datetime.utcnow)
    reviewed_by = Column(GUID(), ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_notes = Column(Text, nullable=True)

    # ASHA Worker assignment & field verification
    assigned_asha_id = Column(GUID(), ForeignKey("users.id"), nullable=True)
    assigned_by = Column(GUID(), ForeignKey("users.id"), nullable=True)
    assigned_at = Column(DateTime, nullable=True)
    verification_status = Column(String(20), default="pending")  # pending, verified, not_confirmed, resolved
    field_observation = Column(Text, nullable=True)
    verified_at = Column(DateTime, nullable=True)
