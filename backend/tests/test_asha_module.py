import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.db.session import Base, engine, get_db
from app.db.seed import seed
from app.models.user import User, UserRole
from app.models.signals import Alert, GeoBlock

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    seed(db)
    yield
    db.close()


def get_auth_header(email: str, password: str = "Demo@1234") -> dict:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, res.text
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_asha_worker_login_and_role():
    """Verify demo ASHA worker can log in and receives role='asha_worker'."""
    res = client.post("/api/v1/auth/login", json={"email": "asha@demo.jagriti", "password": "Demo@1234"})
    assert res.status_code == 200
    data = res.json()
    assert data["user"]["role"] == "asha_worker"
    assert data["user"]["email"] == "asha@demo.jagriti"


def test_rbac_blocks_unauthorized_access():
    """Verify strict RBAC isolation between Citizen, ASHA Worker, and Official roles."""
    citizen_headers = get_auth_header("citizen@demo.jagriti")
    asha_headers = get_auth_header("asha@demo.jagriti")

    # Citizen cannot access ASHA alert endpoints
    res1 = client.get("/api/v1/asha/alerts", headers=citizen_headers)
    assert res1.status_code == 403

    # Citizen cannot access ASHA worker provisioning
    res2 = client.get("/api/v1/asha/workers", headers=citizen_headers)
    assert res2.status_code == 403

    # ASHA worker cannot access Health Official overview
    res3 = client.get("/api/v1/dashboard/gov/overview", headers=asha_headers)
    assert res3.status_code == 403


def test_health_official_assigns_and_asha_verifies_alert():
    """End-to-end flow: Health Official assigns alert -> ASHA verifies in field -> Official sees update."""
    official_headers = get_auth_header("official@demo.jagriti")
    asha_headers = get_auth_header("asha@demo.jagriti")

    # 1. Official scans for alerts
    scan_res = client.post("/api/v1/dashboard/scan", headers=official_headers)
    assert scan_res.status_code == 200

    # 2. Official lists pending alerts
    alerts_res = client.get("/api/v1/dashboard/alerts", headers=official_headers)
    assert alerts_res.status_code == 200
    alerts = alerts_res.json()["alerts"]
    assert len(alerts) > 0
    alert_id = alerts[0]["id"]

    # 3. Official lists ASHA workers and assigns alert
    workers_res = client.get("/api/v1/asha/workers", headers=official_headers)
    assert workers_res.status_code == 200
    workers = workers_res.json()
    assert len(workers) > 0
    asha_id = workers[0]["id"]

    assign_res = client.post(
        f"/api/v1/dashboard/alerts/{alert_id}/assign",
        json={"asha_worker_id": asha_id},
        headers=official_headers,
    )
    assert assign_res.status_code == 200
    assert assign_res.json()["verification_status"] == "pending"

    # 4. ASHA worker views assigned alerts
    my_alerts_res = client.get("/api/v1/asha/alerts", headers=asha_headers)
    assert my_alerts_res.status_code == 200
    assigned_alerts = my_alerts_res.json()
    assert any(a["id"] == alert_id for a in assigned_alerts)

    # 5. ASHA worker submits field verification update
    verify_res = client.post(
        f"/api/v1/asha/alerts/{alert_id}/verify",
        json={
            "verification_status": "verified",
            "field_observation": "Surveyed Niali Block. Identified 3 fever cases and distributed ORS.",
        },
        headers=asha_headers,
    )
    assert verify_res.status_code == 200
    assert verify_res.json()["verification_status"] == "verified"

    # 6. Official confirms updated status on government dashboard
    updated_alerts_res = client.get("/api/v1/dashboard/alerts", headers=official_headers)
    assert updated_alerts_res.status_code == 200
    target_alert = next(a for a in updated_alerts_res.json()["alerts"] if a["id"] == alert_id)
    assert target_alert["verification_status"] == "verified"
    assert "Identified 3 fever cases" in target_alert["field_observation"]


def test_asha_privacy_isolation():
    """Verify ASHA alert payload contains zero citizen PII or raw question texts."""
    official_headers = get_auth_header("official@demo.jagriti")
    asha_headers = get_auth_header("asha@demo.jagriti")

    client.post("/api/v1/dashboard/scan", headers=official_headers)
    alerts = client.get("/api/v1/dashboard/alerts", headers=official_headers).json()["alerts"]
    alert_id = alerts[0]["id"]

    workers = client.get("/api/v1/asha/workers", headers=official_headers).json()
    client.post(
        f"/api/v1/dashboard/alerts/{alert_id}/assign",
        json={"asha_worker_id": workers[0]["id"]},
        headers=official_headers,
    )

    asha_alert = client.get("/api/v1/asha/alerts", headers=asha_headers).json()[0]

    # Privacy assertions: Must not expose citizen name, email, raw query, or exact GPS
    assert "user_name" not in asha_alert
    assert "citizen_email" not in asha_alert
    assert "question_text" not in asha_alert
    assert "exact_location" not in asha_alert
    assert "block_name" in asha_alert
    assert "district" in asha_alert
