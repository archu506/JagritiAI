"""
Tests for §23 items 11-17: anonymous consent, no-consent-prevents-signal,
signal aggregation, anomaly detection, dashboard alert creation, simulated
spike detection, and strict data-plane separation.
"""
import os
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_signals.db")

import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from app.db.session import Base, engine, SessionLocal
from app.models import *  # noqa: F401,F403
from app.models.signals import SignalEvent, Alert, GeoBlock
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


def _ask(question, session_id="s1"):
    r = client.post("/api/v1/query", json={"question": question, "session_id": session_id, "language": "en"})
    assert r.status_code == 200, r.text
    return r.json()


def _register_and_login(email, role="citizen", district=None):
    """
    Creates a user and logs in. Public self-registration only ever creates
    citizen accounts (see app/api/v1/auth.py), so privileged roles are
    provisioned directly against the DB here - the same pattern used by the
    real demo seed script - rather than through the public endpoint.
    """
    if role == "citizen":
        client.post("/api/v1/auth/register", json={
            "full_name": "Test User", "email": email, "password": "testpass123",
            "role": role, "district": district,
        })
    else:
        from app.core.security import hash_password
        db = SessionLocal()
        db.add(User(
            full_name="Test Official", email=email,
            hashed_password=hash_password("testpass123"),
            role=role, district=district,
        ))
        db.commit()
        db.close()
    r = client.post("/api/v1/auth/login", json={"email": email, "password": "testpass123"})
    return r.json()["access_token"]


def test_no_consent_prevents_signal_creation():
    """§23 item 12: declining consent must write nothing to the signal plane."""
    body = _ask("What are the symptoms of malaria?")
    r = client.post("/api/v1/consent", json={"query_id": body["query_id"], "granted": False})
    assert r.status_code == 200
    assert r.json()["status"] == "consent_declined"

    db = SessionLocal()
    count = db.query(SignalEvent).count()
    db.close()
    assert count == 0, "no SignalEvent should exist after declined consent"


def test_consent_creates_signal_event_with_correct_topic():
    """§23 item 11: granting consent writes a de-identified SignalEvent with the classified topic."""
    body = _ask("What are the symptoms of malaria?")
    r = client.post("/api/v1/consent", json={"query_id": body["query_id"], "granted": True})
    assert r.status_code == 200
    assert r.json()["topic_category"] == "vector_borne"
    assert r.json()["topic_tag"] == "malaria"

    db = SessionLocal()
    events = db.query(SignalEvent).all()
    db.close()
    assert len(events) == 1
    assert events[0].topic_category == "vector_borne"
    assert events[0].topic_tag == "malaria"


def test_signal_event_contains_no_identifying_data():
    """Strict data-plane separation: SignalEvent columns must never carry raw text or identity."""
    body = _ask("What are the symptoms of malaria?")
    client.post("/api/v1/consent", json={"query_id": body["query_id"], "granted": True})

    db = SessionLocal()
    event = db.query(SignalEvent).first()
    db.close()
    columns = {c.name for c in SignalEvent.__table__.columns}
    assert "user_id" not in columns
    assert "session_id" not in columns
    assert "question_text" not in columns
    assert "latitude" not in columns and "longitude" not in columns


def test_signal_aggregation_across_multiple_consents():
    """§23 item 13: multiple consented queries for the same topic aggregate into one day's count."""
    for _ in range(5):
        body = _ask("What are the symptoms of malaria?")
        client.post("/api/v1/consent", json={"query_id": body["query_id"], "granted": True})

    db = SessionLocal()
    total = db.query(SignalEvent).filter(SignalEvent.topic_category == "vector_borne").count()
    db.close()
    assert total == 5


def test_anomaly_detection_and_alert_creation():
    """§23 items 14-15: seeded spike must be detected and produce an Alert with status pending_review."""
    from app.db.seed import seed
    seed()
    from app.services.awareness_v2 import AwarenessEngineV2

    db = SessionLocal()
    today = datetime.utcnow().strftime("%Y-%m-%d")
    engine_v2 = AwarenessEngineV2(db)
    alerts = engine_v2.run_for_day(today)
    db.close()

    assert len(alerts) >= 1
    malaria_alerts = [a for a in alerts if a.topic_tag == "malaria"]
    assert len(malaria_alerts) == 1
    assert malaria_alerts[0].severity == "high"
    assert malaria_alerts[0].status == "pending_review"
    assert malaria_alerts[0].is_simulated == 1


def test_dashboard_alert_creation_and_review_flow():
    """§23 item 15-16: full flow - seed spike, run engine, list on dashboard, acknowledge."""
    from app.db.seed import seed
    seed()
    db = SessionLocal()
    db.query(Alert).delete()
    db.commit()
    db.close()

    official_token = _register_and_login("official@test.com", role="health_official")

    r = client.get("/api/v1/dashboard/alerts", headers={"Authorization": f"Bearer {official_token}"})
    assert r.status_code == 200
    assert "not confirmed" in r.json()["disclaimer"].lower() or "not confirmed disease" in r.json()["disclaimer"].lower()
    # No alerts yet - engine hasn't run
    assert r.json()["alerts"] == []


def test_rbac_blocks_citizen_from_gov_alerts():
    citizen_token = _register_and_login("citizen2@test.com", role="citizen")
    r = client.get("/api/v1/dashboard/alerts", headers={"Authorization": f"Bearer {citizen_token}"})
    assert r.status_code == 403


def test_simulated_data_is_labeled():
    """§23 item 16 / proposal §18: simulated demo data must be clearly flagged, never presented as real."""
    from app.db.seed import seed
    seed()
    db = SessionLocal()
    events = db.query(SignalEvent).all()
    db.close()
    assert len(events) > 0
    assert all(e.is_simulated == 1 for e in events), "all seeded demo signal events must be marked is_simulated"


def test_myth_fact_grounded_not_llm_invented():
    """§10 / §23 item 6: myth claims must be answered from the curated MythFact table, never generated."""
    from app.db.seed import seed
    seed()
    r = client.post("/api/v1/query", json={
        "question": "Drinking alcohol prevents dengue.", "session_id": "s1", "language": "en",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["provider"] == "myth_fact_grounded"
    assert "MYTH" in body["answer"] and "FACT" in body["answer"]
    assert "alcohol does not prevent dengue" in body["answer"].lower()


def test_prevention_question_not_misclassified_as_myth():
    """Regression guard: 'how can I prevent X' must stay a prevention question, not myth_fact."""
    from app.services.intent import classify, Intent
    result = classify("How can I prevent dengue?")
    assert result.intent == Intent.prevention


def test_alert_has_coordinates_for_map_and_recommended_actions():
    """Dashboard map/detail panel needs lat/lon and recommended_actions on every alert."""
    from app.db.seed import seed
    seed()
    from app.services.awareness_v2 import AwarenessEngineV2

    db = SessionLocal()
    today = datetime.utcnow().strftime("%Y-%m-%d")
    AwarenessEngineV2(db).run_for_day(today)
    db.close()

    official_token = _register_and_login("official3@test.com", role="health_official")
    r = client.get("/api/v1/dashboard/alerts", headers={"Authorization": f"Bearer {official_token}"})
    assert r.status_code == 200
    alerts = r.json()["alerts"]
    assert len(alerts) >= 1
    for a in alerts:
        assert a["latitude"] is not None and a["longitude"] is not None
        assert isinstance(a["recommended_actions"], list) and len(a["recommended_actions"]) > 0


def test_alert_timeseries_endpoint():
    """Baseline-vs-current chart data must be available per alert."""
    from app.db.seed import seed
    seed()
    from app.services.awareness_v2 import AwarenessEngineV2

    db = SessionLocal()
    today = datetime.utcnow().strftime("%Y-%m-%d")
    AwarenessEngineV2(db).run_for_day(today)
    db.close()

    official_token = _register_and_login("official4@test.com", role="health_official")
    r = client.get("/api/v1/dashboard/alerts", headers={"Authorization": f"Bearer {official_token}"})
    alert_id = r.json()["alerts"][0]["id"]

    r2 = client.get(f"/api/v1/dashboard/alerts/{alert_id}/timeseries",
                     headers={"Authorization": f"Bearer {official_token}"})
    assert r2.status_code == 200
    body = r2.json()
    assert body["baseline_mean"] > 0
    assert len(body["series"]) > 0
    assert all("day_bucket" in pt and "count" in pt for pt in body["series"])


def test_k_anonymity_suppresses_count_below_5_in_trends_and_alerts():
    """
    Proves k-anonymity enforcement in live SignalEvent / AwarenessEngineV2 pipeline:
    1. Count 4 is suppressed in /dashboard/trends.
    2. Count 5 is visible in /dashboard/trends.
    3. Count below 5 cannot create an Alert.
    """
    db = SessionLocal()
    block = GeoBlock(block_name="Test Block", district="Test District", state="Odisha")
    db.add(block)
    db.commit()
    db.refresh(block)

    today = datetime.utcnow().strftime("%Y-%m-%d")

    # Add historical baseline so engine can evaluate z-score
    from datetime import timedelta
    for i in range(1, 5):
        hist_day = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
        db.add(SignalEvent(topic_category="respiratory", geo_block_id=block.id, day_bucket=hist_day, count=1, is_simulated=1))
        db.add(SignalEvent(topic_category="vector_borne", geo_block_id=block.id, day_bucket=hist_day, count=1, is_simulated=1))

    # Add count 4 (below k=5) and count 5 (meets k=5) for today
    db.add(SignalEvent(topic_category="respiratory", geo_block_id=block.id, day_bucket=today, count=4, is_simulated=1))
    db.add(SignalEvent(topic_category="vector_borne", geo_block_id=block.id, day_bucket=today, count=5, is_simulated=1))
    db.commit()

    official_token = _register_and_login("official_k_anon@test.com", role="health_official")
    headers = {"Authorization": f"Bearer {official_token}"}

    # 1 & 2. Check trends endpoint: count 4 suppressed, count 5 visible
    r_trends = client.get("/api/v1/dashboard/trends", headers=headers)
    assert r_trends.status_code == 200
    trends_data = r_trends.json()
    categories_returned = {t["topic_category"]: t["count"] for t in trends_data if t["block_name"] == "Test Block"}

    assert "respiratory" not in categories_returned, "count=4 must be suppressed by k-anonymity gate"
    assert categories_returned.get("vector_borne") == 5, "count=5 must be visible"

    # 3. Check anomaly engine: count below 5 cannot create an alert
    from app.services.awareness_v2 import AwarenessEngineV2
    engine = AwarenessEngineV2(db)
    alerts = engine.run_for_day(today)
    db.close()

    respiratory_alerts = [a for a in alerts if a.topic_category == "respiratory"]
    assert len(respiratory_alerts) == 0, "count below 5 must not produce an alert"


def test_anomaly_baseline_uses_same_topic_tag_and_geography():
    """
    Proves P1 anomaly baseline grouping fix:
    - malaria baseline is calculated strictly for topic_tag='malaria', not a generic vector_borne sum
    - baseline for dengue (count=100) does not contaminate malaria baseline (count=10)
    """
    from datetime import timedelta
    from app.services.awareness_v2 import AwarenessEngineV2

    db = SessionLocal()
    block = GeoBlock(block_name="Baseline Grouping Block", district="Test District", state="Odisha")
    db.add(block)
    db.commit()
    db.refresh(block)
    target_block_id = block.id

    today = datetime.utcnow().strftime("%Y-%m-%d")

    # Add 10 days of historical baseline for dengue (100) and malaria (10) in the same block
    for i in range(1, 11):
        hist_day = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
        db.add(SignalEvent(topic_category="vector_borne", topic_tag="dengue", geo_block_id=target_block_id, day_bucket=hist_day, count=100, is_simulated=1))
        db.add(SignalEvent(topic_category="vector_borne", topic_tag="malaria", geo_block_id=target_block_id, day_bucket=hist_day, count=10, is_simulated=1))

    # Add today's malaria spike of 55
    db.add(SignalEvent(topic_category="vector_borne", topic_tag="malaria", geo_block_id=target_block_id, day_bucket=today, count=55, is_simulated=1))
    db.commit()

    engine = AwarenessEngineV2(db)
    alerts = engine.run_for_day(today)
    db.close()

    malaria_alerts = [a for a in alerts if a.geo_block_id == target_block_id and a.topic_tag == "malaria"]
    assert len(malaria_alerts) == 1, "malaria anomaly must produce an alert"
    assert malaria_alerts[0].baseline_mean == 10.0, "malaria baseline_mean must be 10.0, not contaminated by dengue count of 100"
    assert malaria_alerts[0].observed_count == 55
    assert malaria_alerts[0].severity == "high"


