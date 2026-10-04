"""
End-to-end smoke test of the full demo flow described in the proposal:
register -> login -> ask question (safety+RAG+DemoAI) -> consent ->
anonymized aggregate -> awareness engine -> official review.
Uses SQLite so it runs with zero external services.
"""
import os
os.environ["DATABASE_URL"] = "sqlite:///./test_e2e.db"

import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import Base, engine, SessionLocal
from app.models.knowledge import KnowledgeDocument

import pytest
from app.db.session import Base, engine, get_db
from app.db.seed import seed

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    seed(db)
    yield
    db.close()


def test_full_demo_flow():
    # 1. Register citizen
    citizen_email = f"citizen_{uuid.uuid4().hex[:8]}@test.com"
    r = client.post("/api/v1/auth/register", json={
        "full_name": "Test Citizen", "email": citizen_email,
        "password": "testpass123", "role": "citizen",
        "district": "Khordha", "preferred_language": "en",
    })
    assert r.status_code == 201, r.text

    # 2. Login citizen
    r = client.post("/api/v1/auth/login", json={"email": citizen_email, "password": "testpass123"})
    assert r.status_code == 200, r.text
    citizen_token = r.json()["access_token"]

    # 3. Ask a health question -> safety gate passes -> RAG retrieves -> DemoAI answers
    r = client.post("/api/v1/query", json={
        "question": "I have fever and joint pain, is this dengue?",
        "session_id": "sess-1", "language": "en",
    }, headers={"Authorization": f"Bearer {citizen_token}"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["provider"] == "demo"
    assert body["safety_flag"] == "ok"
    assert "fever" in body["detected_symptom_tags"]
    assert len(body["sources"]) > 0
    query_id = body["query_id"]

    # 3b. Emergency question should be gated, never reach the AI
    r = client.post("/api/v1/query", json={
        "question": "I have chest pain and can't breathe",
        "session_id": "sess-1", "language": "en",
    })
    assert r.status_code == 200
    assert r.json()["safety_flag"] == "emergency"
    assert r.json()["provider"] == "safety_override"

    # 4. Give consent -> anonymized + k-anonymity enforced (won't yet surface with 1 record)
    r = client.post("/api/v1/consent", json={"query_id": query_id, "granted": True},
                     headers={"Authorization": f"Bearer {citizen_token}"})
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "consent_recorded"

    # Manually push the anonymized table over the k-anonymity threshold (5)
    # to prove the awareness engine only fires on non-suppressed aggregates.
    from app.services.privacy import record_anonymized_symptom
    db2 = SessionLocal()
    for _ in range(6):
        record_anonymized_symptom(db2, symptom_tag="fever", district="Khordha")
    # historical baseline weeks so z-score has something to compare against
    from datetime import datetime, timedelta, timezone
    for wk_offset in range(1, 5):
        record_anonymized_symptom(db2, symptom_tag="fever", district="Khordha",
                                   when=datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(weeks=wk_offset))
    db2.close()

    # 5. Provision + login a health official.
    # Public self-registration only ever creates citizen accounts (see
    # app/api/v1/auth.py) - health_official/admin accounts are provisioned
    # directly, the same way the real demo seed script does it.
    from app.core.security import hash_password
    from app.models.user import User

    official_email = f"official_{uuid.uuid4().hex[:8]}@test.com"
    db3 = SessionLocal()
    db3.add(User(
        full_name="Dr. Official", email=official_email,
        hashed_password=hash_password("officialpass123"), role="health_official",
    ))
    db3.commit()
    db3.close()

    r = client.post("/api/v1/auth/login", json={"email": official_email, "password": "officialpass123"})
    official_token = r.json()["access_token"]

    # Reject any attempt to self-register a privileged role via the public endpoint.
    r = client.post("/api/v1/auth/register", json={
        "full_name": "Sneaky Admin", "email": f"sneaky_{uuid.uuid4().hex[:8]}@test.com",
        "password": "sneakypass123", "role": "admin",
    })
    assert r.status_code == 403

    # 6-8. Run Early Awareness Engine, list signals on gov dashboard
    r = client.post("/api/v1/awareness/run",
                     headers={"Authorization": f"Bearer {official_token}"})
    assert r.status_code == 200, r.text

    r = client.get("/api/v1/awareness/signals",
                    headers={"Authorization": f"Bearer {official_token}"})
    assert r.status_code == 200
    signals = r.json()
    assert len(signals) >= 1, "expected at least one early awareness signal"
    assert all(s["status"] == "pending_review" for s in signals)
    signal_id = signals[0]["id"]

    # RBAC check: citizen must NOT be able to access the awareness endpoint
    r = client.get("/api/v1/awareness/signals",
                    headers={"Authorization": f"Bearer {citizen_token}"})
    assert r.status_code == 403

    # 9. Official reviews/acknowledges the signal
    r = client.post(f"/api/v1/awareness/signals/{signal_id}/review",
                     json={"status": "acknowledged", "review_notes": "Verified with district PHC"},
                     headers={"Authorization": f"Bearer {official_token}"})
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "acknowledged"

    print("FULL END-TO-END DEMO FLOW PASSED")


if __name__ == "__main__":
    test_full_demo_flow()
