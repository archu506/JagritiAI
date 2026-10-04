"""
Tests for the topic-aware RAG retrieval pipeline (app/services/rag.py).
These specifically target the disease-mixing failure mode: a semantically
similar but medically WRONG document must never be substituted for the
correct one, and unknown diseases must safely fall back rather than
hallucinate via a near-neighbor document.
"""
import os
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_retrieval.db")

import pytest
from app.db.session import Base, engine, SessionLocal
from app.models import *  # noqa: F401,F403 - registers all tables
from app.db.seed import seed
from app.services.rag import get_retriever


@pytest.fixture(scope="module", autouse=True)
def seeded_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    seed()
    yield


@pytest.fixture
def retriever():
    db = SessionLocal()
    yield get_retriever(db)
    db.close()


def test_malaria_query_returns_malaria_only(retriever):
    results = retriever.retrieve("What are the symptoms of malaria?")
    assert len(results) >= 1
    assert all("Malaria" in r.title for r in results)
    assert not any("Dengue" in r.title for r in results)


def test_dengue_query_returns_dengue_only(retriever):
    results = retriever.retrieve("What are the symptoms of dengue?")
    assert len(results) >= 1
    assert all("Dengue" in r.title for r in results)
    assert not any("Malaria" in r.title for r in results)


def test_unknown_disease_returns_safe_fallback(retriever):
    """Ebola is not in the knowledge base - must return empty, never substitute another disease."""
    results = retriever.retrieve("What are the symptoms of Ebola?")
    assert results == []


def test_generic_fever_does_not_return_dengue(retriever):
    """The core anti-hallucination guarantee: generic symptom queries must not pick a random disease."""
    results = retriever.retrieve("What are the symptoms of fever?")
    assert not any("Dengue" in r.title for r in results)
    assert not any("Malaria" in r.title for r in results)
    # Should hit the generic fever_cluster document instead
    assert any("Fever: General Guidance" in r.title for r in results)


def test_generic_symptom_query_stays_generic(retriever):
    results = retriever.retrieve("I feel unwell with body pain and fatigue")
    assert not any("Dengue" in r.title for r in results)


def test_prevention_intent_still_topic_filtered(retriever):
    results = retriever.retrieve("How can I prevent dengue?")
    assert all("Dengue" in r.title for r in results)


def test_unrelated_disease_source_isolation(retriever):
    """Malaria query must never surface dengue/flu/diabetes docs even via token overlap on 'fever'."""
    results = retriever.retrieve("What are the symptoms of malaria fever?")
    titles = [r.title for r in results]
    assert all("Malaria" in t for t in titles)


def test_low_confidence_query_returns_empty_not_random_doc(retriever):
    results = retriever.retrieve("asdkjaslkdj random gibberish query")
    assert results == []
