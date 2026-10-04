import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.deps import get_current_user, require_roles
from app.core.security import hash_password
from app.models.user import User, UserRole
from app.models.signals import Alert, GeoBlock

router = APIRouter(prefix="/asha", tags=["asha"])

official_or_admin = require_roles(UserRole.health_official, UserRole.admin)
asha_only = require_roles(UserRole.asha_worker)


class AshaWorkerCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=200)
    email: EmailStr
    password: str = Field(..., min_length=8)
    district: Optional[str] = None
    state: Optional[str] = None


class VerifyAlertPayload(BaseModel):
    verification_status: str  # pending, verified, not_confirmed, resolved
    field_observation: Optional[str] = None


@router.get("/workers")
def list_asha_workers(db: Session = Depends(get_db), current_user: User = Depends(official_or_admin)):
    """List ASHA workers, scoped to current official's district if specified."""
    query = db.query(User).filter(User.role == UserRole.asha_worker)
    if current_user.role == UserRole.health_official and current_user.district:
        query = query.filter(User.district == current_user.district)
    workers = query.all()
    return [
        {
            "id": w.id,
            "full_name": w.full_name,
            "email": w.email,
            "district": w.district,
            "state": w.state,
        }
        for w in workers
    ]


@router.post("/workers", status_code=status.HTTP_201_CREATED)
def create_asha_worker(payload: AshaWorkerCreate, db: Session = Depends(get_db), current_user: User = Depends(official_or_admin)):
    """Provision a new ASHA worker account (Official or Admin only)."""
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="User with this email already exists")

    district = payload.district or current_user.district
    state = payload.state or current_user.state or "Odisha"

    worker = User(
        full_name=payload.full_name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=UserRole.asha_worker,
        district=district,
        state=state,
    )
    db.add(worker)
    db.commit()
    db.refresh(worker)
    return {
        "id": worker.id,
        "full_name": worker.full_name,
        "email": worker.email,
        "role": worker.role.value,
        "district": worker.district,
    }


@router.get("/alerts")
def list_assigned_alerts(db: Session = Depends(get_db), current_user: User = Depends(asha_only)):
    """
    List Early Awareness Alerts assigned to the currently authenticated ASHA worker.
    Strict privacy isolation: returns ONLY coarse block-level anomaly statistics.
    Zero citizen PII, zero raw question text, zero exact GPS coordinates.
    """
    rows = (
        db.query(Alert, GeoBlock)
        .join(GeoBlock, Alert.geo_block_id == GeoBlock.id)
        .filter(Alert.assigned_asha_id == current_user.id)
        .order_by(Alert.generated_at.desc())
        .all()
    )

    return [
        {
            "id": alert.id,
            "topic_category": alert.topic_category,
            "topic_tag": alert.topic_tag,
            "block_name": block.block_name,
            "district": block.district,
            "state": block.state,
            "latitude": block.latitude,
            "longitude": block.longitude,
            "period_bucket": alert.period_bucket,
            "observed_count": alert.observed_count,
            "baseline_mean": alert.baseline_mean,
            "z_score": alert.z_score,
            "severity": alert.severity,
            "status": alert.status,
            "verification_status": alert.verification_status or "pending",
            "field_observation": alert.field_observation,
            "assigned_at": alert.assigned_at,
            "verified_at": alert.verified_at,
            "generated_at": alert.generated_at,
        }
        for alert, block in rows
    ]


@router.post("/alerts/{alert_id}/verify")
def verify_alert_field_status(
    alert_id: str,
    payload: VerifyAlertPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(asha_only),
):
    """
    ASHA worker updates ground verification status (pending, verified, not_confirmed, resolved)
    and submits field observation notes.
    """
    valid_statuses = ("pending", "verified", "not_confirmed", "resolved")
    if payload.verification_status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"verification_status must be one of {valid_statuses}",
        )

    alert = (
        db.query(Alert)
        .filter(Alert.id == alert_id, Alert.assigned_asha_id == current_user.id)
        .first()
    )
    if not alert:
        raise HTTPException(
            status_code=404,
            detail="Alert not found or not assigned to you",
        )

    alert.verification_status = payload.verification_status
    alert.field_observation = payload.field_observation
    alert.verified_at = datetime.utcnow()
    db.commit()
    db.refresh(alert)

    return {
        "id": alert.id,
        "verification_status": alert.verification_status,
        "field_observation": alert.field_observation,
        "verified_at": alert.verified_at,
    }
