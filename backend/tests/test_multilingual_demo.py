"""
Tests for multilingual Demo Mode knowledge retrieval and medical safety overrides
across English (en), Hindi (hi), and Odia (or).
"""
import os
os.environ["DATABASE_URL"] = "sqlite:///./test_multilingual.db"

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import Base, engine, SessionLocal
from app.db.seed import seed

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    seed()
    yield


def test_dengue_prevention_english():
    r = client.post("/api/v1/query", json={
        "question": "How can I prevent dengue?",
        "session_id": "test-en-dengue-prev",
        "language": "en",
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["safety_flag"] == "ok"
    assert body["provider"] == "demo"
    assert "dengue" in body["answer"].lower() or "mosquito" in body["answer"].lower()
    assert len(body["sources"]) > 0
    assert any("NCDC" in s["source_name"] or "Dengue" in s["title"] for s in body["sources"])


def test_dengue_prevention_hindi():
    r = client.post("/api/v1/query", json={
        "question": "डेंगू से कैसे बचें?",
        "session_id": "test-hi-dengue-prev",
        "language": "hi",
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["safety_flag"] == "ok"
    assert body["provider"] == "demo"
    assert "डेंगू" in body["answer"] or "मच्छर" in body["answer"]
    assert "सत्यापित" in body["answer"]
    assert len(body["sources"]) > 0
    assert any("NCDC" in s["source_name"] or "डेंगू" in s["title"] for s in body["sources"])


def test_dengue_prevention_odia():
    r = client.post("/api/v1/query", json={
        "question": "ଡେଙ୍ଗୁରୁ କିପରି ରକ୍ଷା ପାଇବେ?",
        "session_id": "test-or-dengue-prev",
        "language": "or",
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["safety_flag"] == "ok"
    assert body["provider"] == "demo"
    assert "ଡେଙ୍ଗୁ" in body["answer"] or "ମଶା" in body["answer"]
    assert len(body["sources"]) > 0


def test_malaria_prevention_hindi_and_odia():
    # Hindi
    r_hi = client.post("/api/v1/query", json={
        "question": "मलेरिया से कैसे बचें?",
        "session_id": "test-hi-malaria-prev",
        "language": "hi",
    })
    assert r_hi.status_code == 200
    body_hi = r_hi.json()
    assert body_hi["safety_flag"] == "ok"
    assert "मलेरिया" in body_hi["answer"] or "मच्छर" in body_hi["answer"]

    # Odia
    r_or = client.post("/api/v1/query", json={
        "question": "ମ୍ୟାଲେରିଆ ପ୍ରତିଷେଧକ",
        "session_id": "test-or-malaria-prev",
        "language": "or",
    })
    assert r_or.status_code == 200
    body_or = r_or.json()
    assert body_or["safety_flag"] == "ok"
    assert "ମ୍ୟାଲେରିଆ" in body_or["answer"] or "ମଶା" in body_or["answer"]


def test_fever_awareness_multilingual():
    for lang, q in [
        ("en", "What should I do if I have a fever?"),
        ("hi", "बुखार होने पर क्या करें?"),
        ("or", "ଜ୍ୱର ହେଲେ କ’ଣ କରିବେ?"),
    ]:
        r = client.post("/api/v1/query", json={"question": q, "session_id": f"fever-{lang}", "language": lang})
        assert r.status_code == 200
        body = r.json()
        assert body["safety_flag"] == "ok"
        assert len(body["sources"]) > 0


def test_diarrhea_ors_awareness_multilingual():
    for lang, q in [
        ("en", "What is ORS and how to manage diarrhea?"),
        ("hi", "दस्त और ओआरएस की जानकारी"),
        ("or", "ଝାଡ଼ା ଏବଂ ଓଆରଏସ୍"),
    ]:
        r = client.post("/api/v1/query", json={"question": q, "session_id": f"diarrhea-{lang}", "language": lang})
        assert r.status_code == 200
        body = r.json()
        assert body["safety_flag"] == "ok"
        assert len(body["sources"]) > 0


def test_emergency_warning_triggers_safety_override():
    emergency_queries = [
        ("en", "I have severe chest pain and difficulty breathing."),
        ("hi", "मुझे छाती में दर्द है और सांस नहीं आ रही है"),
        ("or", "ମୋର ଛାତିରେ ଯନ୍ତ୍ରଣା ଏବଂ ଶ୍ୱାସକ୍ରିୟାରେ କଷ୍ଟ ହେଉଛି"),
    ]
    for lang, q in emergency_queries:
        r = client.post("/api/v1/query", json={"question": q, "session_id": f"emg-{lang}", "language": lang})
        assert r.status_code == 200
        body = r.json()
        assert body["safety_flag"] == "emergency"
        assert body["provider"] == "safety_override"
        assert "108" in body["answer"]
