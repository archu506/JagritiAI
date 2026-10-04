import json
from datetime import datetime
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.core.config import settings
from app.core.deps import get_current_user, require_roles
from app.models.user import User, UserRole
from app.models.health import HealthQuery, AnonymizedSymptomReport, EarlyAwarenessSignal
from app.models.signals import SignalEvent, Alert, GeoBlock
from app.services.privacy import get_k_anonymous_aggregates
from app.services.awareness_v2 import recommended_actions

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
official_or_admin = require_roles(UserRole.health_official, UserRole.admin)


@router.get("/citizen/history")
def citizen_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Citizen dashboard: their own past questions and answers."""
    queries = (
        db.query(HealthQuery)
        .filter(HealthQuery.user_id == current_user.id)
        .order_by(HealthQuery.created_at.desc())
        .limit(50)
        .all()
    )
    return [
        {
            "id": q.id,
            "question": q.question_text,
            "answer": q.ai_response_text,
            "language": q.language.value if hasattr(q.language, "value") else q.language,
            "safety_flag": q.safety_flag,
            "contributed_to_public_health": q.contributed_to_public_health,
            "created_at": q.created_at,
        }
        for q in queries
    ]


@router.get("/gov/overview")
def gov_overview(db: Session = Depends(get_db), current_user: User = Depends(official_or_admin)):
    """
    Government dashboard: k-anonymous aggregate trend summary plus current
    early awareness signals. Never exposes individual-level data.
    """
    aggregates = get_k_anonymous_aggregates(db)
    trend = [
        {"symptom_tag": a.symptom_tag, "district_bucket": a.district_bucket, "week_bucket": a.week_bucket, "count": a.count}
        for a in aggregates
    ]

    signal_counts = (
        db.query(EarlyAwarenessSignal.severity, func.count(EarlyAwarenessSignal.id))
        .filter(EarlyAwarenessSignal.status == "pending_review")
        .group_by(EarlyAwarenessSignal.severity)
        .all()
    )

    total_queries = db.query(func.count(HealthQuery.id)).scalar()

    return {
        "trend": trend,
        "pending_signals_by_severity": {sev: count for sev, count in signal_counts},
        "total_citizen_queries": total_queries,
    }


# --- New signal-plane endpoints (§20 API structure) ---

@router.post("/scan")
def run_awareness_scan_v2(
    day_bucket: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(official_or_admin),
):
    """
    Runs AwarenessEngineV2 (signal plane) for the given day, or today by
    default. Produces Alert rows - see GET /dashboard/alerts to view them.
    """
    from app.services.awareness_v2 import AwarenessEngineV2
    day = day_bucket or datetime.utcnow().strftime("%Y-%m-%d")
    engine_v2 = AwarenessEngineV2(db)
    alerts = engine_v2.run_for_day(day)
    return {"day_bucket": day, "alerts_generated": len(alerts)}


@router.get("/trends")
def gov_trends(
    topic_category: str | None = None,
    district: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(official_or_admin),
):
    """
    Aggregate signal-plane trend, optionally filtered by topic_category
    and/or district. Reads ONLY from SignalEvent/GeoBlock (signal plane) -
    never touches HealthQuery (conversation plane).
    Enforces K_ANONYMITY_THRESHOLD so small groups (<5) are suppressed.
    """
    query = (
        db.query(
            SignalEvent.topic_category, SignalEvent.topic_tag,
            GeoBlock.block_name, GeoBlock.district, GeoBlock.latitude, GeoBlock.longitude,
            SignalEvent.day_bucket,
            func.sum(SignalEvent.count).label("total"),
            func.max(SignalEvent.is_simulated).label("is_simulated"),
        )
        .join(GeoBlock, SignalEvent.geo_block_id == GeoBlock.id)
        .group_by(
            SignalEvent.topic_category, SignalEvent.topic_tag,
            GeoBlock.block_name, GeoBlock.district, GeoBlock.latitude, GeoBlock.longitude,
            SignalEvent.day_bucket,
        )
        .having(func.sum(SignalEvent.count) >= settings.K_ANONYMITY_THRESHOLD)
    )
    if topic_category:
        query = query.filter(SignalEvent.topic_category == topic_category)
    if district:
        query = query.filter(GeoBlock.district.ilike(f"%{district}%"))

    rows = query.all()
    return [
        {
            "topic_category": r.topic_category, "topic_tag": r.topic_tag,
            "block_name": r.block_name, "district": r.district,
            "latitude": r.latitude, "longitude": r.longitude,
            "day_bucket": r.day_bucket, "count": int(r.total),
            "is_simulated": bool(r.is_simulated),
        }
        for r in rows
        if r.total >= settings.K_ANONYMITY_THRESHOLD
    ]


@router.get("/alerts")
def gov_alerts(
    status: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(official_or_admin),
):
    """
    List Early Awareness Alerts (signal plane only). Every alert response
    explicitly carries a disclaimer - this is never a confirmed outbreak.
    Enforces K_ANONYMITY_THRESHOLD so alerts below threshold (<5) are suppressed.
    """
    query = db.query(Alert, GeoBlock).join(GeoBlock, Alert.geo_block_id == GeoBlock.id).filter(Alert.observed_count >= settings.K_ANONYMITY_THRESHOLD)
    if status:
        query = query.filter(Alert.status == status)
    rows = query.order_by(Alert.z_score.desc()).all()

    # Pre-fetch ASHA names for assigned alerts
    asha_ids = [alert.assigned_asha_id for alert, _ in rows if alert.assigned_asha_id]
    asha_names = {}
    if asha_ids:
        asha_users = db.query(User.id, User.full_name).filter(User.id.in_(asha_ids)).all()
        asha_names = {u.id: u.full_name for u in asha_users}

    return {
        "disclaimer": "These are early awareness signals based on statistical anomalies in "
                      "anonymized, aggregated query volume. They are NOT confirmed disease "
                      "outbreaks and require human/public-health verification.",
        "alerts": [
            {
                "id": alert.id, "topic_category": alert.topic_category, "topic_tag": alert.topic_tag,
                "block_name": block.block_name, "district": block.district,
                "latitude": block.latitude, "longitude": block.longitude,
                "period_bucket": alert.period_bucket, "observed_count": alert.observed_count,
                "baseline_mean": alert.baseline_mean, "z_score": alert.z_score,
                "severity": alert.severity, "status": alert.status,
                "is_simulated": bool(alert.is_simulated), "generated_at": alert.generated_at,
                "recommended_actions": recommended_actions(alert.severity),
                "assigned_asha_id": alert.assigned_asha_id,
                "assigned_asha_name": asha_names.get(alert.assigned_asha_id),
                "assigned_at": alert.assigned_at,
                "verification_status": alert.verification_status or "pending",
                "field_observation": alert.field_observation,
                "verified_at": alert.verified_at,
            }
            for alert, block in rows
        ],
    }


@router.post("/alerts/{alert_id}/timeseries")
@router.get("/alerts/{alert_id}/timeseries")
def alert_timeseries(
    alert_id: str,
    days: int = 28,
    db: Session = Depends(get_db),
    current_user: User = Depends(official_or_admin),
):
    """
    Daily signal-event counts for this alert's (topic_category, geo_block)
    pair over the trailing `days` window, for a baseline-vs-current chart.
    """
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    rows = (
        db.query(SignalEvent.day_bucket, func.sum(SignalEvent.count).label("total"))
        .filter(
            SignalEvent.topic_category == alert.topic_category,
            SignalEvent.geo_block_id == alert.geo_block_id,
        )
        .group_by(SignalEvent.day_bucket)
        .order_by(SignalEvent.day_bucket)
        .all()
    )
    return {
        "alert_id": alert_id,
        "baseline_mean": alert.baseline_mean,
        "series": [{"day_bucket": r.day_bucket, "count": int(r.total)} for r in rows],
    }


@router.post("/alerts/{alert_id}/ack")
def acknowledge_alert(
    alert_id: str,
    status: str = "acknowledged",
    review_notes: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(official_or_admin),
):
    """Human-in-the-loop review step - the system never auto-confirms an outbreak."""
    if status not in ("acknowledged", "dismissed"):
        raise HTTPException(status_code=400, detail="status must be 'acknowledged' or 'dismissed'")

    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.status = status
    alert.reviewed_by = current_user.id
    alert.reviewed_at = datetime.utcnow()
    alert.review_notes = review_notes
    db.commit()
    db.refresh(alert)
    return {"id": alert.id, "status": alert.status, "reviewed_at": alert.reviewed_at}


@router.post("/broadcast")
def broadcast_awareness_content(
    alert_id: str,
    message: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(official_or_admin),
):
    """
    Simulated for MVP (per proposal §19): records that an official chose to
    push localized prevention content in response to an alert. Does not
    actually send push notifications/SMS in this build.
    """
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {
        "status": "broadcast_simulated",
        "alert_id": alert_id,
        "message": message,
        "note": "MVP simulation only - no real push/SMS was sent.",
    }


class AssignAlertPayload(BaseModel):
    asha_worker_id: str


@router.post("/alerts/{alert_id}/assign")
def assign_alert_to_asha(
    alert_id: str,
    payload: AssignAlertPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(official_or_admin),
):
    """Assign an Early Awareness Alert to an ASHA worker for field verification."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    asha = db.query(User).filter(User.id == payload.asha_worker_id, User.role == UserRole.asha_worker).first()
    if not asha:
        raise HTTPException(status_code=400, detail="Target user is not a valid ASHA worker")

    alert.assigned_asha_id = asha.id
    alert.assigned_by = current_user.id
    alert.assigned_at = datetime.utcnow()
    alert.verification_status = "pending"
    db.commit()
    db.refresh(alert)

    return {
        "id": alert.id,
        "assigned_asha_id": str(asha.id),
        "assigned_asha_name": asha.full_name,
        "assigned_at": alert.assigned_at,
        "verification_status": alert.verification_status,
    }
