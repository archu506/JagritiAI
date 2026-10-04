import uuid
from sqlalchemy import Column, String, Text, Float
from app.db.types import GUID
from app.db.session import Base


class HealthScheme(Base):
    __tablename__ = "health_schemes"
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(300), nullable=False)
    description = Column(Text, nullable=False)
    eligibility = Column(Text, nullable=False)
    how_to_apply = Column(Text, nullable=False)
    official_url = Column(String(500), nullable=True)
    language = Column(String(5), default="en")


class MythFact(Base):
    __tablename__ = "myth_facts"
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    myth = Column(Text, nullable=False)
    fact = Column(Text, nullable=False)
    topic_tag = Column(String(100), index=True)
    source_name = Column(String(200), nullable=True)
    language = Column(String(5), default="en")


class HealthFacility(Base):
    """
    Demo-mode facility directory. In production, MapService would call a
    real maps/geocoding API (see services/maps.py); DemoMapService serves
    this static, seeded directory instead so 'nearby healthcare' works
    fully offline.
    """
    __tablename__ = "health_facilities"
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(300), nullable=False)
    facility_type = Column(String(50), nullable=False)  # PHC, CHC, District Hospital, etc.
    district = Column(String(100), nullable=False, index=True)
    state = Column(String(100), nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    phone = Column(String(20), nullable=True)
