import math
from abc import ABC, abstractmethod
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.content import HealthFacility
from app.core.config import settings


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


class MapService(ABC):
    @abstractmethod
    def nearby_facilities(self, db: Session, district: str, lat: Optional[float], lon: Optional[float], limit: int = 10) -> List[HealthFacility]:
        raise NotImplementedError


class DemoMapService(MapService):
    """
    Offline: serves from the seeded HealthFacility table. If lat/lon given,
    ranks by straight-line distance; otherwise filters by district name.
    No external Maps API key required.
    """

    def nearby_facilities(self, db: Session, district: str, lat=None, lon=None, limit=10):
        query = db.query(HealthFacility)
        if district:
            query = query.filter(HealthFacility.district.ilike(f"%{district}%"))
        facilities = query.all()

        if lat is not None and lon is not None:
            facilities = [f for f in facilities if f.latitude is not None and f.longitude is not None]
            facilities.sort(key=lambda f: haversine_km(lat, lon, f.latitude, f.longitude))

        return facilities[:limit]


class GoogleMapsService(MapService):
    """
    Real implementation placeholder - would call Google Places/Directions API
    using settings.MAPS_API_KEY. Falls back to DemoMapService if unavailable.
    """

    def __init__(self):
        self._fallback = DemoMapService()

    def nearby_facilities(self, db: Session, district: str, lat=None, lon=None, limit=10):
        # Real implementation would call the Places API here.
        return self._fallback.nearby_facilities(db, district, lat, lon, limit)


def get_map_service() -> MapService:
    if settings.MAPS_API_KEY:
        return GoogleMapsService()
    return DemoMapService()
