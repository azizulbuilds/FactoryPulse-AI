import sys
from pathlib import Path

import pytest


# Make the backend application importable from the project root.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_PATH = PROJECT_ROOT / "apps" / "backend"

sys.path.insert(0, str(BACKEND_PATH))

from app.services.alert_rules import evaluate_sensor_reading
from app.services.machine_health import calculate_machine_health


@pytest.fixture
def normal_reading():
    """A sensor reading that triggers no demonstration rules."""

    return {
        "machine_id": "MACHINE-001",
        "air_temperature": 298.5,
        "process_temperature": 308.2,
        "rotational_speed": 1500,
        "torque": 42.3,
        "tool_wear": 100,
    }


@pytest.fixture
def critical_reading():
    """A reading that triggers four demonstration alert rules."""

    return {
        "machine_id": "MACHINE-002",
        "air_temperature": 298.5,
        "process_temperature": 325,
        "rotational_speed": 1100,
        "torque": 72,
        "tool_wear": 260,
    }


def test_normal_reading_generates_no_alerts(normal_reading):
    alerts = evaluate_sensor_reading(normal_reading)

    assert alerts == []


def test_critical_reading_generates_four_alerts(critical_reading):
    alerts = evaluate_sensor_reading(critical_reading)

    assert len(alerts) == 4

    severities = [alert["severity"] for alert in alerts]

    assert severities.count("critical") == 3
    assert severities.count("warning") == 1


def test_alerts_contain_required_fields(critical_reading):
    alerts = evaluate_sensor_reading(critical_reading)

    required_fields = {
        "machine_id",
        "severity",
        "title",
        "message",
        "threshold",
    }

    for alert in alerts:
        assert required_fields.issubset(alert.keys())
        assert alert["machine_id"] == "MACHINE-002"


def test_normal_machine_health_score(normal_reading):
    result = calculate_machine_health(normal_reading)

    assert result["health_score"] == 100.0
    assert result["condition"] == "healthy"
    assert result["scoring_method"] == "rule_based"


def test_critical_machine_health_score(critical_reading):
    result = calculate_machine_health(critical_reading)

    assert result["health_score"] == 10.0
    assert result["condition"] == "critical"


def test_health_score_never_exceeds_valid_range(critical_reading):
    result = calculate_machine_health(critical_reading)

    assert 0 <= result["health_score"] <= 100