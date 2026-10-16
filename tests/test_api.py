import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_PATH = PROJECT_ROOT / "apps" / "backend"

sys.path.insert(0, str(BACKEND_PATH))

from app.main import app


client = TestClient(app)


@pytest.fixture
def normal_reading():
    return {
        "machine_id": "API-TEST-NORMAL",
        "air_temperature": 298.5,
        "process_temperature": 308.2,
        "rotational_speed": 1500,
        "torque": 42.3,
        "tool_wear": 100,
    }


@pytest.fixture
def critical_reading():
    return {
        "machine_id": "API-TEST-CRITICAL",
        "air_temperature": 298.5,
        "process_temperature": 325,
        "rotational_speed": 1100,
        "torque": 72,
        "tool_wear": 260,
    }


def test_root_endpoint():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["status"] == "running"


def test_monitoring_stores_normal_reading(normal_reading):
    response = client.post(
        "/api/v1/monitoring/readings",
        json=normal_reading,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["machine_id"] == "API-TEST-NORMAL"
    assert data["status"] == "received"
    assert data["alerts_generated"] == 0


def test_monitoring_generates_critical_alerts(critical_reading):
    response = client.post(
        "/api/v1/monitoring/readings",
        json=critical_reading,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["machine_id"] == "API-TEST-CRITICAL"
    assert data["alerts_generated"] == 4


def test_reading_history_endpoint():
    response = client.get(
        "/api/v1/monitoring/readings",
        params={"machine_id": "API-TEST-NORMAL"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["count"] >= 1
    assert all(
        item["machine_id"] == "API-TEST-NORMAL"
        for item in data["items"]
    )


def test_machine_health_endpoint(normal_reading):
    # Ensure the machine has a stored reading.
    client.post(
        "/api/v1/monitoring/readings",
        json=normal_reading,
    )

    response = client.get(
        "/api/v1/machine-health/API-TEST-NORMAL"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["health_score"] == 100.0
    assert data["condition"] == "healthy"


def test_unknown_machine_returns_404():
    response = client.get(
        "/api/v1/machine-health/MACHINE-DOES-NOT-EXIST"
    )

    assert response.status_code == 404


def test_fleet_overview_endpoint():
    response = client.get("/api/v1/fleet/overview")

    assert response.status_code == 200

    data = response.json()

    assert "summary" in data
    assert "machines" in data
    assert "total_machines" in data["summary"]


def test_alert_listing_endpoint():
    response = client.get(
        "/api/v1/alerts",
        params={"machine_id": "API-TEST-CRITICAL"},
    )

    assert response.status_code == 200

    data = response.json()
    print("\nAlert API response:", data)

    # Support either a direct list or a dictionary containing alerts.
    if isinstance(data, dict):
        alerts = data.get("alerts", data.get("items", []))
    else:
        alerts = data

    assert isinstance(alerts, list), (
        f"Expected a list of alerts, received: {type(alerts).__name__}"
    )

    assert len(alerts) >= 1

    assert all(
        alert["machine_id"] == "API-TEST-CRITICAL"
        for alert in alerts
    )