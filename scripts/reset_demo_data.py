"""Safely replace test records with a three-machine FactoryPulse AI demo fleet.

Run from the repository root:
    python scripts/reset_demo_data.py

The script requires apps/backend/data/factorypulse.backup.db to exist, creates
an additional timestamped SQLite backup, asks for an explicit confirmation,
and uses the existing alert_rules.evaluate_sensor_reading function to generate
alerts for each machine's latest reading.
"""

from __future__ import annotations

import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = PROJECT_ROOT / "apps" / "backend" / "data" / "factorypulse.db"
REQUIRED_BACKUP = PROJECT_ROOT / "apps" / "backend" / "data" / "factorypulse.backup.db"

# Make the existing FastAPI application package importable when invoked from
# the project root, without changing the user's environment.
sys.path.insert(0, str(PROJECT_ROOT / "apps" / "backend"))

try:
    from app.services.alert_rules import evaluate_sensor_reading
except Exception as exc:  # pragma: no cover - error path depends on local environment
    raise SystemExit(
        "Could not import the existing alert rules. Run this command from the "
        "project root with the project's Python environment activated.\n"
        f"Details: {exc}"
    ) from exc


# Each machine has five illustrative telemetry samples. Samples are explicitly
# demo data; alerts are generated only for each machine's latest sample.
DEMO_MACHINES = [
    {
        "machine_id": "CNC-MILL-001",
        "readings": [
            {"air_temperature": 298.2, "process_temperature": 306.8, "rotational_speed": 1510, "torque": 40.0, "tool_wear": 96},
            {"air_temperature": 298.3, "process_temperature": 307.2, "rotational_speed": 1520, "torque": 40.8, "tool_wear": 97},
            {"air_temperature": 298.4, "process_temperature": 307.6, "rotational_speed": 1505, "torque": 41.5, "tool_wear": 98},
            {"air_temperature": 298.4, "process_temperature": 308.0, "rotational_speed": 1515, "torque": 42.0, "tool_wear": 99},
            {"air_temperature": 298.5, "process_temperature": 308.2, "rotational_speed": 1500, "torque": 42.3, "tool_wear": 100},
        ],
    },
    {
        "machine_id": "PRECISION-LATHE-001",
        "readings": [
            {"air_temperature": 298.3, "process_temperature": 311.4, "rotational_speed": 1580, "torque": 54.0, "tool_wear": 207},
            {"air_temperature": 298.4, "process_temperature": 312.5, "rotational_speed": 1560, "torque": 56.0, "tool_wear": 211},
            {"air_temperature": 298.4, "process_temperature": 313.8, "rotational_speed": 1540, "torque": 58.0, "tool_wear": 216},
            {"air_temperature": 298.5, "process_temperature": 315.4, "rotational_speed": 1530, "torque": 60.5, "tool_wear": 221},
            {"air_temperature": 298.5, "process_temperature": 316.2, "rotational_speed": 1520, "torque": 62.0, "tool_wear": 225},
        ],
    },
    {
        "machine_id": "HYDRAULIC-PRESS-001",
        "readings": [
            {"air_temperature": 299.0, "process_temperature": 318.0, "rotational_speed": 1300, "torque": 58.0, "tool_wear": 215},
            {"air_temperature": 299.2, "process_temperature": 320.0, "rotational_speed": 1250, "torque": 62.0, "tool_wear": 228},
            {"air_temperature": 299.5, "process_temperature": 322.0, "rotational_speed": 1190, "torque": 66.0, "tool_wear": 240},
            {"air_temperature": 299.7, "process_temperature": 324.0, "rotational_speed": 1150, "torque": 70.0, "tool_wear": 252},
            {"air_temperature": 300.0, "process_temperature": 325.0, "rotational_speed": 1100, "torque": 72.0, "tool_wear": 260},
        ],
    },
]


def create_backup(db_path: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = db_path.with_name(f"factorypulse.pre-demo-{timestamp}.db")
    with sqlite3.connect(db_path) as source, sqlite3.connect(backup_path) as target:
        source.backup(target)
    return backup_path


def main() -> None:
    if not DATABASE_PATH.exists():
        raise SystemExit(f"Database not found: {DATABASE_PATH}")
    if not REQUIRED_BACKUP.exists():
        raise SystemExit(
            "Expected backup file was not found:\n"
            f"{REQUIRED_BACKUP}\n"
            "Create and verify a backup before running this cleanup."
        )

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    try:
        tables = {
            row["name"]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        if not {"sensor_readings", "alerts"}.issubset(tables):
            raise SystemExit(
                "The expected sensor_readings and alerts tables were not found. "
                "No records have been changed."
            )

        current_readings = connection.execute(
            "SELECT COUNT(*) FROM sensor_readings"
        ).fetchone()[0]
        current_alerts = connection.execute(
            "SELECT COUNT(*) FROM alerts"
        ).fetchone()[0]

        print("FactoryPulse AI demo data reset")
        print(f"Database: {DATABASE_PATH}")
        print(f"Verified existing backup: {REQUIRED_BACKUP}")
        print(f"Current records: {current_readings} sensor readings, {current_alerts} alerts")
        print("Planned result: 15 illustrative readings for 3 demo machines.")
        print("Alerts will be generated by the project's existing alert rules for the latest reading of each machine.")
        confirmation = input("Type RESET-DEMO-DATA to continue: ").strip()
        if confirmation != "RESET-DEMO-DATA":
            print("Cancelled. No records were changed.")
            return

        additional_backup = create_backup(DATABASE_PATH)
        print(f"Additional backup created: {additional_backup}")

        now = datetime.now(timezone.utc)
        prepared_readings: list[tuple[str, dict[str, float], str]] = []
        latest_by_machine: dict[str, dict[str, float]] = {}

        # Insert samples chronologically per machine; each machine's newest row
        # is therefore the one the fleet endpoint will select by MAX(id).
        for machine in DEMO_MACHINES:
            machine_id = machine["machine_id"]
            readings = machine["readings"]
            for index, values in enumerate(readings):
                minutes_ago = (len(readings) - index - 1) * 12
                received_at = (now - timedelta(minutes=minutes_ago)).isoformat()
                prepared_readings.append((machine_id, values, received_at))
            latest_by_machine[machine_id] = readings[-1]

        connection.execute("BEGIN IMMEDIATE")
        connection.execute("DELETE FROM alerts")
        connection.execute("DELETE FROM sensor_readings")

        for machine_id, values, received_at in prepared_readings:
            connection.execute(
                """
                INSERT INTO sensor_readings (
                    machine_id, air_temperature, process_temperature,
                    rotational_speed, torque, tool_wear, received_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    machine_id,
                    values["air_temperature"],
                    values["process_temperature"],
                    values["rotational_speed"],
                    values["torque"],
                    values["tool_wear"],
                    received_at,
                ),
            )

        created_alerts = 0
        for machine_id, values in latest_by_machine.items():
            reading_data = {"machine_id": machine_id, **values}
            generated_alerts = evaluate_sensor_reading(reading_data)
            latest_timestamp = connection.execute(
                "SELECT received_at FROM sensor_readings WHERE machine_id = ? ORDER BY id DESC LIMIT 1",
                (machine_id,),
            ).fetchone()["received_at"]

            for alert in generated_alerts:
                connection.execute(
                    """
                    INSERT INTO alerts (
                        machine_id, severity, title, message,
                        anomaly_score, threshold, status, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, 'open', ?)
                    """,
                    (
                        alert.get("machine_id", machine_id),
                        alert.get("severity", "warning"),
                        alert.get("title", "Machine requires review"),
                        alert.get("message", "Review the latest machine telemetry."),
                        alert.get("anomaly_score"),
                        alert.get("threshold"),
                        latest_timestamp,
                    ),
                )
                created_alerts += 1

        connection.commit()

        print("\nDemo data reset complete.")
        print(f"Sensor readings inserted: {len(prepared_readings)}")
        print(f"Alerts generated by existing rules: {created_alerts}")
        print("Machines:")
        for machine_id in latest_by_machine:
            print(f"  - {machine_id}")
        print("\nRestart FastAPI, then verify GET /api/v1/fleet/overview in Swagger.")
        print("All telemetry values are illustrative demo data, not real factory measurements.")
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    main()
