import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Float
from app.db.types import GUID
from app.db.session import Base


class KnowledgeDocument(Base):
    """
    A verified health-information source chunk used for RAG retrieval.
    In production this is mirrored into a vector store (Qdrant); embedding_id
    links to that external vector. Locally we fall back to keyword search
    (see services/rag.py DemoRetriever) when no vector store is configured.

    topic_tag: specific disease/topic (e.g. 'dengue') OR a generic marker
        (e.g. 'fever_general') for category-level documents with no single
        named disease.
    category: coarse HealthCategory bucket (see services/taxonomy.py) -
        used to answer generic symptom queries without guessing a disease.
    authority_score: 0-100, higher = more authoritative source (e.g. WHO/
        MoHFW/NCDC ranked above less official bodies). Used in re-ranking.
    """
    __tablename__ = "knowledge_documents"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    title = Column(String(300), nullable=False)
    content = Column(Text, nullable=False)
    source_name = Column(String(200), nullable=False)  # e.g. "MoHFW", "WHO", "NCDC"
    source_url = Column(String(500), nullable=True)
    topic_tag = Column(String(100), nullable=False, index=True)  # e.g. 'dengue', 'fever_general'
    category = Column(String(50), nullable=False, index=True, default="other")
    language = Column(String(5), default="en")
    embedding_id = Column(String(100), nullable=True)
    authority_score = Column(Float, default=50.0)
    published_date = Column(String(10), nullable=True)  # ISO date string, e.g. '2025-06-01'
    created_at = Column(DateTime, default=datetime.utcnow)

