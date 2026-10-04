from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.health import AnonymizedSymptomReport
from app.core.config import settings


def iso_week_bucket(dt: datetime) -> str:
    iso = dt.isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"


def record_anonymized_symptom(
    db: Session,
    symptom_tag: str,
    district: str | None,
    age_bucket: str | None = None,
    when: datetime | None = None,
) -> AnonymizedSymptomReport:
    """
    Writes a de-identified symptom record. No user_id, name, email, or exact
    location is stored - only a generalized district bucket and ISO week.
    Called only after explicit user consent (see ConsentRecord).
    """
    when = when or datetime.utcnow()
    district_bucket = (district or "unspecified").strip().title()

    record = AnonymizedSymptomReport(
        symptom_tag=symptom_tag,
        district_bucket=district_bucket,
        age_bucket=age_bucket,
        week_bucket=iso_week_bucket(when),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_k_anonymous_aggregates(db: Session, week_bucket: str | None = None):
    """
    Returns (symptom_tag, district_bucket, week_bucket, count) rows, but
    SUPPRESSES any group whose count is below K_ANONYMITY_THRESHOLD so that
    small groups (which could re-identify individuals in sparse districts)
    are never exposed via the dashboard or the Early Awareness Engine.
    """
    query = db.query(
        AnonymizedSymptomReport.symptom_tag,
        AnonymizedSymptomReport.district_bucket,
        AnonymizedSymptomReport.week_bucket,
        func.count(AnonymizedSymptomReport.id).label("count"),
    ).group_by(
        AnonymizedSymptomReport.symptom_tag,
        AnonymizedSymptomReport.district_bucket,
        AnonymizedSymptomReport.week_bucket,
    )

    if week_bucket:
        query = query.filter(AnonymizedSymptomReport.week_bucket == week_bucket)

    rows = query.all()
    return [r for r in rows if r.count >= settings.K_ANONYMITY_THRESHOLD]
