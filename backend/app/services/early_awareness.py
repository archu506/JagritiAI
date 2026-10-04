import statistics
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.health import AnonymizedSymptomReport, EarlyAwarenessSignal
from app.services.privacy import get_k_anonymous_aggregates

Z_SCORE_THRESHOLDS = {"low": 2.0, "moderate": 3.0, "high": 4.0}


def _severity_from_z(z: float) -> str | None:
    if z >= Z_SCORE_THRESHOLDS["high"]:
        return "high"
    if z >= Z_SCORE_THRESHOLDS["moderate"]:
        return "moderate"
    if z >= Z_SCORE_THRESHOLDS["low"]:
        return "low"
    return None


def _historical_counts(db: Session, symptom_tag: str, district_bucket: str, exclude_week: str) -> list[int]:
    """Weekly counts for this (symptom, district) pair, excluding the week being evaluated."""
    rows = (
        db.query(AnonymizedSymptomReport.week_bucket)
        .filter(
            AnonymizedSymptomReport.symptom_tag == symptom_tag,
            AnonymizedSymptomReport.district_bucket == district_bucket,
            AnonymizedSymptomReport.week_bucket != exclude_week,
        )
        .all()
    )
    counts: dict[str, int] = {}
    for (week,) in rows:
        counts[week] = counts.get(week, 0) + 1
    return list(counts.values())


class EarlyAwarenessEngine:
    """
    Computes a z-score of the current week's symptom count against the
    historical weekly baseline for the same (symptom, district) pair, using
    only k-anonymous aggregated data (never raw per-user records).

    IMPORTANT: This produces an *Early Awareness Signal*, not a confirmed
    outbreak diagnosis. Every signal is written with status='pending_review'
    and must be acknowledged by a human health_official before it carries
    any operational weight - see api/v1/awareness.py.
    """

    def __init__(self, db: Session):
        self.db = db

    def run_for_week(self, week_bucket: str) -> list[EarlyAwarenessSignal]:
        aggregates = get_k_anonymous_aggregates(self.db, week_bucket=week_bucket)
        signals = []

        for row in aggregates:
            history = _historical_counts(self.db, row.symptom_tag, row.district_bucket, week_bucket)
            if len(history) < 3:
                continue  # not enough baseline data to judge an anomaly

            mean = statistics.mean(history)
            stddev = statistics.pstdev(history) or 1.0  # avoid divide-by-zero
            z = (row.count - mean) / stddev
            severity = _severity_from_z(z)

            if severity is None:
                continue

            signal = EarlyAwarenessSignal(
                symptom_tag=row.symptom_tag,
                district_bucket=row.district_bucket,
                week_bucket=week_bucket,
                observed_count=row.count,
                baseline_mean=mean,
                baseline_stddev=stddev,
                z_score=z,
                severity=severity,
                status="pending_review",
            )
            self.db.add(signal)
            signals.append(signal)

        self.db.commit()
        for s in signals:
            self.db.refresh(s)
        return signals
