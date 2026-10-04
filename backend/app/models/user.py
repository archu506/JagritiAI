import enum
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Enum, ForeignKey, Text
from app.db.types import GUID
from sqlalchemy.orm import relationship
from app.db.session import Base


class UserRole(str, enum.Enum):
    citizen = "citizen"
    health_official = "health_official"
    asha_worker = "asha_worker"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    full_name = Column(String(200), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.citizen)
    preferred_language = Column(String(5), default="en")
    district = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    consents = relationship("ConsentRecord", back_populates="user")
    queries = relationship("HealthQuery", back_populates="user")


class ConsentRecord(Base):
    __tablename__ = "consent_records"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    purpose = Column(String(100), nullable=False, default="public_health_contribution")
    granted = Column(Boolean, default=False)
    granted_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="consents")
