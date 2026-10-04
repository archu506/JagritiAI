from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.deps import require_roles
from app.models.user import UserRole, User
from app.models.health import EarlyAwarenessSignal
from app.schemas.health import AwarenessSignalOut, AwarenessReviewRequest
from app.services.early_awareness import EarlyAwarenessEngine
from app.services.privacy import iso_week_bucket

router = APIRouter(prefix="/awareness", tags=["awareness"])

official_or_admin = require_roles(UserRole.health_official, UserRole.admin)


@router.post("/run", response_model=list[AwarenessSignalOut])
def run_awareness_scan(
    week_bucket: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(official_or_admin),
):
    """
    Core demo flow, step 6-7:
    Aggregated trend -> Early Awareness Engine analyzes it -> anomaly signals
    are generated (status='pending_review'). Restricted to health officials/admins.
    """
    week = week_bucket or iso_week_bucket(datetime.utcnow())
    engine = EarlyAwarenessEngine(db)
    return engine.run_for_week(week)


@router.get("/signals", response_model=list[AwarenessSignalOut])
def list_signals(
    status: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(official_or_admin),
):
    """
    Core demo flow, step 8: Government dashboard displays awareness signals.
    """
    query = db.query(EarlyAwarenessSignal)
    if status:
        query = query.filter(EarlyAwarenessSignal.status == status)
    return query.order_by(EarlyAwarenessSignal.z_score.desc()).all()


@router.post("/signals/{signal_id}/review", response_model=AwarenessSignalOut)
def review_signal(
    signal_id: str,
    payload: AwarenessReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(official_or_admin),
):
    """
    Core demo flow, step 9: Official reviews/acknowledges the signal.
    This is a human decision - the system never auto-confirms an outbreak.
    """
    if payload.status not in ("acknowledged", "dismissed"):
        raise HTTPException(status_code=400, detail="status must be 'acknowledged' or 'dismissed'")

    signal = db.query(EarlyAwarenessSignal).filter(EarlyAwarenessSignal.id == signal_id).first()
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")

    signal.status = payload.status
    signal.reviewed_by = current_user.id
    signal.reviewed_at = datetime.utcnow()
    signal.review_notes = payload.review_notes
    db.commit()
    db.refresh(signal)
    return signal
