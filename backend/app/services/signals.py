"""
The one-way write path from CONVERSATION PLANE -> SIGNAL PLANE.

record_signal_event() is the only function anywhere in the codebase that is
allowed to write to SignalEvent. It:
  1. Never receives or stores user_id, session_id, raw question text, or
     exact location - callers must already have reduced to
     (topic_category, topic_tag, district) before calling this.
  2. Only runs when the citizen has explicitly granted consent (enforced by
     the caller in api/v1/consent.py - this function has no consent logic
     of its own, by design, so there is exactly one gate to audit).
  3. Resolves district name -> GeoBlock (creating a demo block if needed),
     so the signal plane never stores free-text location.
"""
from datetime import datetime, date
from sqlalchemy.orm import Session
from app.models.signals import GeoBlock, SignalEvent


def get_or_create_geo_block(db: Session, district: str | None) -> GeoBlock:
    district_name = (district or "Unspecified").strip().title()
    block = db.query(GeoBlock).filter(GeoBlock.district == district_name).first()
    if block:
        return block
    block = GeoBlock(block_name=f"{district_name} (District-level)", district=district_name, state="Unspecified")
    db.add(block)
    db.commit()
    db.refresh(block)
    return block


def record_signal_event(
    db: Session,
    topic_category: str,
    topic_tag: str | None,
    district: str | None,
    when: datetime | None = None,
    is_simulated: bool = False,
) -> SignalEvent:
    when = when or datetime.utcnow()
    geo_block = get_or_create_geo_block(db, district)
    day_bucket = when.strftime("%Y-%m-%d")

    event = SignalEvent(
        topic_category=topic_category,
        topic_tag=topic_tag,
        geo_block_id=geo_block.id,
        day_bucket=day_bucket,
        count=1,
        is_simulated=1 if is_simulated else 0,
        created_at=when,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event
