import statistics
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.signals import SignalEvent, Alert, GeoBlock
from app.core.config import settings

Z_SCORE_THRESHOLDS = {"low": 2.0, "moderate": 3.0, "high": 4.0}


def _severity_from_z(z: float) -> str | None:
    if z >= Z_SCORE_THRESHOLDS["high"]:
        return "high"
    if z >= Z_SCORE_THRESHOLDS["moderate"]:
        return "moderate"
    if z >= Z_SCORE_THRESHOLDS["low"]:
        return "low"
    return None


RECOMMENDED_ACTIONS = {
    "high": [
        "Verify signal through field health workers before any public communication",
        "Deploy a rapid response/surveillance team to the affected block",
        "Increase local vector-control or hygiene measures based on topic category",
    ],
    "moderate": [
        "Monitor the area closely over the next reporting period",
        "Alert the district health office for awareness",
        "Consider targeted prevention messaging in the affected block",
    ],
    "low": [
        "Continue routine monitoring",
        "No immediate action required beyond standard surveillance",
    ],
}


def recommended_actions(severity: str) -> list[str]:
    return RECOMMENDED_ACTIONS.get(severity, RECOMMENDED_ACTIONS["low"])


class AwarenessEngineV2:
    """
    Detects unusual increases in aggregated, anonymized health-topic signal
    volume for a given (topic_category, geo_block) pair, comparing the most
    recent day_bucket's count against a rolling historical baseline.

    IMPORTANT: produces an Alert with status='pending_review' - never a
    confirmed-outbreak claim. See models/signals.py Alert docstring.
    """

    def __init__(self, db: Session, baseline_days: int = 28):
        self.db = db
        self.baseline_days = baseline_days

    def _baseline_counts(
        self, topic_category: str, topic_tag: str | None, geo_block_id, exclude_day: str
    ) -> list[int]:
        query = (
            self.db.query(SignalEvent.day_bucket, func.sum(SignalEvent.count))
            .filter(
                SignalEvent.topic_category == topic_category,
                SignalEvent.geo_block_id == geo_block_id,
                SignalEvent.day_bucket != exclude_day,
            )
        )
        if topic_tag is not None:
            query = query.filter(SignalEvent.topic_tag == topic_tag)
        else:
            query = query.filter(SignalEvent.topic_tag.is_(None))

        rows = query.group_by(SignalEvent.day_bucket).all()
        return [int(total) for _, total in rows]

    def run_for_day(self, day_bucket: str) -> list[Alert]:
        current_rows = (
            self.db.query(
                SignalEvent.topic_category, SignalEvent.topic_tag, SignalEvent.geo_block_id,
                func.sum(SignalEvent.count).label("total"),
                func.max(SignalEvent.is_simulated).label("is_simulated"),
            )
            .filter(SignalEvent.day_bucket == day_bucket)
            .group_by(SignalEvent.topic_category, SignalEvent.topic_tag, SignalEvent.geo_block_id)
            .having(func.sum(SignalEvent.count) >= settings.K_ANONYMITY_THRESHOLD)
            .all()
        )

        alerts = []
        for topic_category, topic_tag, geo_block_id, total, is_simulated in current_rows:
            if total < settings.K_ANONYMITY_THRESHOLD:
                continue  # Enforce k-anonymity gate: suppress signals below threshold (< 5)

            history = self._baseline_counts(topic_category, topic_tag, geo_block_id, day_bucket)
            if len(history) < 3:
                continue  # not enough baseline to judge an anomaly

            mean = statistics.mean(history)
            stddev = statistics.pstdev(history) or 1.0
            z = (total - mean) / stddev
            severity = _severity_from_z(z)
            if severity is None:
                continue

            existing_alerts_query = (
                self.db.query(Alert)
                .filter(
                    Alert.topic_category == topic_category,
                    Alert.geo_block_id == geo_block_id,
                    Alert.period_bucket == day_bucket,
                )
            )
            if topic_tag is not None:
                existing_alerts_query = existing_alerts_query.filter(Alert.topic_tag == topic_tag)
            else:
                existing_alerts_query = existing_alerts_query.filter(Alert.topic_tag.is_(None))
            existing_alerts = existing_alerts_query.all()

            if existing_alerts:
                # Prefer keeping an alert with an ASHA assignment or non-pending verification status
                target_alert = next(
                    (a for a in existing_alerts if a.assigned_asha_id or a.verification_status != "pending"),
                    existing_alerts[0]
                )
                # Remove any duplicate alert rows for the same group
                for extra in existing_alerts:
                    if extra.id != target_alert.id:
                        self.db.delete(extra)

                target_alert.topic_tag = topic_tag
                target_alert.observed_count = int(total)
                target_alert.baseline_mean = mean
                target_alert.baseline_stddev = stddev
                target_alert.z_score = z
                target_alert.severity = severity
                target_alert.is_simulated = int(is_simulated or 0)
                alerts.append(target_alert)
            else:
                alert = Alert(
                    topic_category=topic_category,
                    topic_tag=topic_tag,
                    geo_block_id=geo_block_id,
                    period_bucket=day_bucket,
                    observed_count=int(total),
                    baseline_mean=mean,
                    baseline_stddev=stddev,
                    z_score=z,
                    severity=severity,
                    status="pending_review",
                    is_simulated=int(is_simulated or 0),
                )
                self.db.add(alert)
                alerts.append(alert)

        self.db.commit()
        for a in alerts:
            self.db.refresh(a)
        return alerts
