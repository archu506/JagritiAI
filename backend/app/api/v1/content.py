from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.content import HealthScheme, MythFact
from app.services.maps import get_map_service

router = APIRouter(prefix="/content", tags=["content"])


@router.get("/schemes")
def list_schemes(language: str = "en", db: Session = Depends(get_db)):
    schemes = db.query(HealthScheme).filter(HealthScheme.language == language).all()
    return [
        {
            "id": s.id, "name": s.name, "description": s.description,
            "eligibility": s.eligibility, "how_to_apply": s.how_to_apply,
            "official_url": s.official_url,
        }
        for s in schemes
    ]


@router.get("/myths")
def list_myths(topic_tag: Optional[str] = None, language: str = "en", db: Session = Depends(get_db)):
    query = db.query(MythFact).filter(MythFact.language == language)
    if topic_tag:
        query = query.filter(MythFact.topic_tag == topic_tag)
    myths = query.all()
    return [
        {"id": m.id, "myth": m.myth, "fact": m.fact, "topic_tag": m.topic_tag, "source_name": m.source_name}
        for m in myths
    ]


@router.get("/facilities/nearby")
def nearby_facilities(
    district: str = Query(...),
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    db: Session = Depends(get_db),
):
    service = get_map_service()
    facilities = service.nearby_facilities(db, district=district, lat=lat, lon=lon)
    return [
        {
            "id": f.id, "name": f.name, "facility_type": f.facility_type,
            "district": f.district, "state": f.state,
            "latitude": f.latitude, "longitude": f.longitude, "phone": f.phone,
        }
        for f in facilities
    ]
