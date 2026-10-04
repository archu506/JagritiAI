import requests
import json

BASE_URL = "http://localhost:8000"

def run_test():
    print("--- 1. Health check ---")
    r = requests.get(f"{BASE_URL}/health")
    print(f"Health: {r.status_code} {r.json()}")
    assert r.status_code == 200

    print("\n--- 2. Login as Official ---")
    r = requests.post(f"{BASE_URL}/api/v1/auth/login", json={"email": "official@demo.jagriti", "password": "Demo@1234"})
    assert r.status_code == 200, f"Official login failed: {r.text}"
    official_token = r.json()["access_token"]
    official_headers = {"Authorization": f"Bearer {official_token}"}
    print("Official logged in successfully.")

    print("\n--- 3. Get alerts as Official ---")
    r = requests.get(f"{BASE_URL}/api/v1/dashboard/alerts", headers=official_headers)
    assert r.status_code == 200, f"Get alerts failed: {r.text}"
    alerts_data = r.json()
    alerts = alerts_data.get("alerts", [])
    print(f"Total alerts retrieved by official: {len(alerts)}")
    malaria_alert = None
    for a in alerts:
        print(f"Alert ID: {a['id']}, Tag: {a.get('topic_tag')}, Block: {a.get('block_name')}, Assigned: {a.get('assigned_asha_id')}")
        if a.get("topic_tag") == "malaria":
            malaria_alert = a
    
    assert malaria_alert is not None, "Malaria alert not found!"
    alert_id = malaria_alert["id"]
    print(f"\nMalaria Alert found ID: {alert_id}")
    print(f"Observed: {malaria_alert.get('observed_count')}, Baseline: {malaria_alert.get('baseline_mean')}, Z: {malaria_alert.get('z_score')}, Severity: {malaria_alert.get('severity')}")

    print("\n--- 4. Assign Alert to Demo ASHA Worker ---")
    asha_id = "241ebf25-831d-46cc-b62e-ddbfae055760"
    r = requests.post(f"{BASE_URL}/api/v1/dashboard/alerts/{alert_id}/assign", json={"asha_worker_id": asha_id}, headers=official_headers)
    assert r.status_code == 200, f"Assign failed: {r.status_code} {r.text}"
    print(f"Assign response: {r.json()}")

    print("\n--- 5. Login as ASHA Worker ---")
    r = requests.post(f"{BASE_URL}/api/v1/auth/login", json={"email": "asha@demo.jagriti", "password": "Demo@1234"})
    assert r.status_code == 200, f"ASHA login failed: {r.text}"
    asha_token = r.json()["access_token"]
    asha_headers = {"Authorization": f"Bearer {asha_token}"}
    print("ASHA logged in successfully.")

    print("\n--- 6. GET /api/v1/asha/alerts ---")
    r = requests.get(f"{BASE_URL}/api/v1/asha/alerts", headers=asha_headers)
    assert r.status_code == 200, f"GET /asha/alerts failed: {r.status_code} {r.text}"
    asha_alerts = r.json()
    print(f"ASHA Alerts Count: {len(asha_alerts)}")
    print(json.dumps(asha_alerts, indent=2))
    assert len(asha_alerts) == 1, f"Expected 1 alert for ASHA worker, got {len(asha_alerts)}"
    assigned_alert = asha_alerts[0]
    assert assigned_alert["topic_tag"] == "malaria"
    assert assigned_alert["block_name"] == "Niali Block"
    assert assigned_alert["district"] == "Cuttack"
    assert assigned_alert["observed_count"] == 55
    assert assigned_alert["baseline_mean"] == 12.0
    assert round(assigned_alert["z_score"], 2) == 7.02
    assert assigned_alert["severity"] == "high"
    assert assigned_alert["verification_status"] == "pending"

    print("\n--- 7. Trigger Scan POST /api/v1/dashboard/scan ---")
    r = requests.post(f"{BASE_URL}/api/v1/dashboard/scan", headers=official_headers)
    assert r.status_code == 200, f"Scan failed: {r.status_code} {r.text}"
    print(f"Scan response: {r.json()}")

    print("\n--- 8. GET /api/v1/asha/alerts AFTER scan ---")
    r = requests.get(f"{BASE_URL}/api/v1/asha/alerts", headers=asha_headers)
    assert r.status_code == 200
    asha_alerts_after = r.json()
    print(f"ASHA Alerts Count after scan: {len(asha_alerts_after)}")
    assert len(asha_alerts_after) == 1, "Alert assignment was lost after scan!"
    assert asha_alerts_after[0]["id"] == alert_id, "Alert ID changed after scan!"
    assert asha_alerts_after[0]["verification_status"] == "pending", "Verification status changed after scan!"

    print("\n✅ LIVE E2E TEST PASSED PERFECTLY!")

if __name__ == "__main__":
    run_test()
