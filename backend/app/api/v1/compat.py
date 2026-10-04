"""
Thin compatibility aliases matching the exact endpoint names from the
product spec (§20), delegating to the existing implementations so there is
only one real code path per feature. Added rather than renaming the
original routes, per instruction to preserve existing API behavior.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.deps import get_optional_user
from app.schemas.health import QueryRequest, QueryResponse
from app.api.v1.query import ask_question
from app.api.v1.content import nearby_facilities, list_schemes

router = APIRouter(prefix="", tags=["compat"])


@router.post("/chat/message", response_model=QueryResponse)
def chat_message(payload: QueryRequest, db: Session = Depends(get_db), user=Depends(get_optional_user)):
    """Alias for POST /query, matching the spec's /chat/message naming."""
    return ask_question(payload, db, user)


@router.get("/facilities/nearby")
def facilities_nearby_alias(district: str, lat: float | None = None, lon: float | None = None, db: Session = Depends(get_db)):
    """Alias for GET /content/facilities/nearby, matching the spec's /facilities/nearby naming."""
    return nearby_facilities(district=district, lat=lat, lon=lon, db=db)


@router.get("/schemes/search")
def schemes_search_alias(language: str = "en", db: Session = Depends(get_db)):
    """Alias for GET /content/schemes, matching the spec's /schemes/search naming."""
    return list_schemes(language=language, db=db)
