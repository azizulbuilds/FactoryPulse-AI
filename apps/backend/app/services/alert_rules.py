from typing import Any


# Demonstration thresholds only.
# These are not validated operating limits for real industrial equipment.

PROCESS_TEMP_WARNING = 315.0
PROCESS_TEMP_CRITICAL = 323.0

TORQUE_WARNING = 60.0
TORQUE_CRITICAL = 70.0

TOOL_WEAR_WARNING = 220.0
TOOL_WEAR_CRITICAL = 250.0

MIN_ROTATIONAL_SPEED = 1200.0
MAX_ROTATIONAL_SPEED = 2500.0


def evaluate_sensor_reading(
    reading: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Evaluate a machine sensor reading against demonstration rules.

    Returns a list of rule-based alerts.

    This function does not use a trained ML model.
    """

    alerts: list[dict[str, Any]] = []

    machine_id = str(reading.get("machine_id", "UNKNOWN"))

    process_temperature = float(
        reading["process_temperature"]
    )

    torque = float(reading["torque"])

    tool_wear = float(reading["tool_wear"])

    rotational_speed = float(
        reading["rotational_speed"]
    )

    # Rule 1: Process temperature
    if process_temperature >= PROCESS_TEMP_CRITICAL:
        alerts.append(
            {
                "machine_id": machine_id,
                "severity": "critical",
                "title": "Critical process temperature",
                "message": (
                    f"Machine {machine_id} has a process temperature "
                    f"of {process_temperature:.1f} K, meeting or "
                    f"exceeding the demonstration threshold of "
                    f"{PROCESS_TEMP_CRITICAL:.1f} K."
                ),
                "threshold": PROCESS_TEMP_CRITICAL,
            }
        )

    elif process_temperature >= PROCESS_TEMP_WARNING:
        alerts.append(
            {
                "machine_id": machine_id,
                "severity": "warning",
                "title": "High process temperature",
                "message": (
                    f"Machine {machine_id} has a process temperature "
                    f"of {process_temperature:.1f} K, meeting or "
                    f"exceeding the demonstration threshold of "
                    f"{PROCESS_TEMP_WARNING:.1f} K."
                ),
                "threshold": PROCESS_TEMP_WARNING,
            }
        )

    # Rule 2: Torque
    if torque >= TORQUE_CRITICAL:
        alerts.append(
            {
                "machine_id": machine_id,
                "severity": "critical",
                "title": "Critical torque level",
                "message": (
                    f"Machine {machine_id} has torque of "
                    f"{torque:.1f} Nm, meeting or exceeding the "
                    f"demonstration threshold of "
                    f"{TORQUE_CRITICAL:.1f} Nm."
                ),
                "threshold": TORQUE_CRITICAL,
            }
        )

    elif torque >= TORQUE_WARNING:
        alerts.append(
            {
                "machine_id": machine_id,
                "severity": "warning",
                "title": "High torque level",
                "message": (
                    f"Machine {machine_id} has torque of "
                    f"{torque:.1f} Nm, meeting or exceeding the "
                    f"demonstration threshold of "
                    f"{TORQUE_WARNING:.1f} Nm."
                ),
                "threshold": TORQUE_WARNING,
            }
        )

    # Rule 3: Tool wear
    if tool_wear >= TOOL_WEAR_CRITICAL:
        alerts.append(
            {
                "machine_id": machine_id,
                "severity": "critical",
                "title": "Critical tool wear",
                "message": (
                    f"Machine {machine_id} has tool wear of "
                    f"{tool_wear:.1f} minutes, meeting or exceeding "
                    f"the demonstration threshold of "
                    f"{TOOL_WEAR_CRITICAL:.1f} minutes."
                ),
                "threshold": TOOL_WEAR_CRITICAL,
            }
        )

    elif tool_wear >= TOOL_WEAR_WARNING:
        alerts.append(
            {
                "machine_id": machine_id,
                "severity": "warning",
                "title": "High tool wear",
                "message": (
                    f"Machine {machine_id} has tool wear of "
                    f"{tool_wear:.1f} minutes, meeting or exceeding "
                    f"the demonstration threshold of "
                    f"{TOOL_WEAR_WARNING:.1f} minutes."
                ),
                "threshold": TOOL_WEAR_WARNING,
            }
        )

    # Rule 4: Rotational speed
    if rotational_speed < MIN_ROTATIONAL_SPEED:
        alerts.append(
            {
                "machine_id": machine_id,
                "severity": "warning",
                "title": "Low rotational speed",
                "message": (
                    f"Machine {machine_id} has rotational speed of "
                    f"{rotational_speed:.1f} RPM, below the "
                    f"demonstration threshold of "
                    f"{MIN_ROTATIONAL_SPEED:.1f} RPM."
                ),
                "threshold": MIN_ROTATIONAL_SPEED,
            }
        )

    elif rotational_speed > MAX_ROTATIONAL_SPEED:
        alerts.append(
            {
                "machine_id": machine_id,
                "severity": "warning",
                "title": "High rotational speed",
                "message": (
                    f"Machine {machine_id} has rotational speed of "
                    f"{rotational_speed:.1f} RPM, above the "
                    f"demonstration threshold of "
                    f"{MAX_ROTATIONAL_SPEED:.1f} RPM."
                ),
                "threshold": MAX_ROTATIONAL_SPEED,
            }
        )

    return alerts