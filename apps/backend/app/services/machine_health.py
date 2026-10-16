from typing import Any


def calculate_machine_health(
    reading: dict[str, Any],
) -> dict[str, Any]:
    """
    Calculate a demonstration machine health score from sensor readings.

    Score range: 0–100.
    This is a rule-based indicator, not a trained ML prediction.
    """

    score = 100.0
    reasons = []

    process_temperature = float(
        reading["process_temperature"]
    )
    rotational_speed = float(
        reading["rotational_speed"]
    )
    torque = float(reading["torque"])
    tool_wear = float(reading["tool_wear"])

    # Process temperature
    if process_temperature >= 323:
        score -= 30
        reasons.append("Critical process temperature")
    elif process_temperature >= 315:
        score -= 15
        reasons.append("High process temperature")

    # Torque
    if torque >= 70:
        score -= 25
        reasons.append("Critical torque")
    elif torque >= 60:
        score -= 12
        reasons.append("High torque")

    # Tool wear
    if tool_wear >= 250:
        score -= 25
        reasons.append("Critical tool wear")
    elif tool_wear >= 220:
        score -= 12
        reasons.append("High tool wear")

    # Rotational speed
    if rotational_speed < 1200:
        score -= 10
        reasons.append("Low rotational speed")
    elif rotational_speed > 2500:
        score -= 10
        reasons.append("High rotational speed")

    score = max(0, min(100, score))

    if score >= 85:
        condition = "healthy"
    elif score >= 60:
        condition = "attention_required"
    else:
        condition = "critical"

    if not reasons:
        reasons.append("No configured threshold violations")

    return {
        "machine_id": reading.get(
            "machine_id",
            "UNKNOWN",
        ),
        "health_score": round(score, 1),
        "condition": condition,
        "reasons": reasons,
        "scoring_method": "rule_based",
    }