import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.deps import get_optional_user
from app.schemas.health import ConsentRequest
from app.models.health import HealthQuery
from app.models.user import ConsentRecord
from app.services.privacy import record_anonymized_symptom
from app.services.signals import record_signal_event

router = APIRouter(prefix="/consent", tags=["consent"])


@router.post("")
def give_consent(payload: ConsentRequest, db: Session = Depends(get_db), user=Depends(get_optional_user)):
    """
    Core demo flow, step 4-5:
    User gives optional public-health contribution consent.

    This is the ONLY place in the codebase that triggers a write to the
    SIGNAL PLANE (see services/signals.py). If granted, we write a
    SignalEvent containing ONLY topic_category/topic_tag + coarse district +
    day bucket - never the raw question text, user identity, or exact
    location. If declined, nothing is written to the signal plane at all
    and the query stays confined to the conversation plane.
    """
    query = db.query(HealthQuery).filter(HealthQuery.id == payload.query_id).first()
    if not query:
        raise HTTPException(status_code=404, detail="Query not found")

    if user:
        consent = ConsentRecord(
            user_id=user.id,
            purpose="public_health_contribution",
            granted=payload.granted,
            granted_at=datetime.utcnow() if payload.granted else None,
        )
        db.add(consent)

    if not payload.granted:
        db.commit()
        return {"status": "consent_declined"}

    district = user.district if user else None

    # New signal-plane write (topic_category-based, matches Early Awareness
    # Engine's aggregation unit).
    if query.topic_category:
        record_signal_event(
            db, topic_category=query.topic_category, topic_tag=query.topic_tag, district=district,
        )

    # Legacy symptom-tag-based write, preserved for backward compatibility
    # with the original AnonymizedSymptomReport/EarlyAwarenessSignal path
    # and existing tests that exercise it directly.
    tags = json.loads(query.detected_symptom_tags or "[]")
    for tag in tags:
        record_anonymized_symptom(
            db, symptom_tag=tag, district=district, age_bucket=payload.age_bucket
        )

    query.contributed_to_public_health = True
    db.commit()

    return {
        "status": "consent_recorded",
        "topic_category": query.topic_category,
        "topic_tag": query.topic_tag,
        "symptom_tags_contributed": tags,
    }

