import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.services.alert_rules import evaluate_sensor_reading


router = APIRouter(
    prefix="/monitoring",
    tags=["Machine Monitoring"],
)


PROJECT_ROOT = Path(__file__).resolve().parents[4]

DATABASE_PATH = (
    PROJECT_ROOT
    / "apps"
    / "backend"
    / "data"
    / "factorypulse.db"
)


# -----------------------------
# Database initialization
# -----------------------------

def get_connection():
    DATABASE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS sensor_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            machine_id TEXT NOT NULL,
            air_temperature REAL NOT NULL,
            process_temperature REAL NOT NULL,
            rotational_speed REAL NOT NULL,
            torque REAL NOT NULL,
            tool_wear REAL NOT NULL,
            received_at TEXT NOT NULL
        )
        """
    )

    connection.commit()

    return connection


def initialize_alert_table(connection):
    """
    Ensure the alert table exists.

    The schema must remain compatible with alerts.py.
    """

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            machine_id TEXT NOT NULL,
            severity TEXT NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            anomaly_score REAL,
            threshold REAL,
            status TEXT NOT NULL DEFAULT 'open',
            created_at TEXT NOT NULL
        )
        """
    )

    connection.commit()


def row_to_dict(row):
    return dict(row)


# -----------------------------
# Request and response models
# -----------------------------

class SensorReading(BaseModel):
    machine_id: str = Field(
        min_length=1,
        max_length=50,
    )

    air_temperature: float = Field(gt=0)
    process_temperature: float = Field(gt=0)
    rotational_speed: float = Field(gt=0)
    torque: float = Field(ge=0)
    tool_wear: float = Field(ge=0)


class MonitoringResponse(BaseModel):
    machine_id: str
    status: Literal["received"]
    received_at: datetime
    sensor_readings: dict[str, float]
    alerts_generated: int
    alerts: list[dict]


# -----------------------------
# Submit sensor readings
# -----------------------------

@router.post(
    "/readings",
    response_model=MonitoringResponse,
)
def receive_sensor_reading(reading: SensorReading):
    received_at = datetime.now(timezone.utc)

    sensor_values = {
        "air_temperature": reading.air_temperature,
        "process_temperature": reading.process_temperature,
        "rotational_speed": reading.rotational_speed,
        "torque": reading.torque,
        "tool_wear": reading.tool_wear,
    }

    reading_data = {
        "machine_id": reading.machine_id,
        **sensor_values,
    }

    generated_alerts = evaluate_sensor_reading(
        reading_data
    )

    # Save the reading and its generated alerts together.
    with closing(get_connection()) as connection:
        initialize_alert_table(connection)

        connection.execute(
            """
            INSERT INTO sensor_readings (
                machine_id,
                air_temperature,
                process_temperature,
                rotational_speed,
                torque,
                tool_wear,
                received_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                reading.machine_id,
                reading.air_temperature,
                reading.process_temperature,
                reading.rotational_speed,
                reading.torque,
                reading.tool_wear,
                received_at.isoformat(),
            ),
        )

        for alert in generated_alerts:
            connection.execute(
                """
                INSERT INTO alerts (
                    machine_id,
                    severity,
                    title,
                    message,
                    anomaly_score,
                    threshold,
                    status,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    alert["machine_id"],
                    alert["severity"],
                    alert["title"],
                    alert["message"],
                    None,
                    alert["threshold"],
                    "open",
                    received_at.isoformat(),
                ),
            )

        connection.commit()

    return MonitoringResponse(
        machine_id=reading.machine_id,
        status="received",
        received_at=received_at,
        sensor_readings=sensor_values,
        alerts_generated=len(generated_alerts),
        alerts=generated_alerts,
    )


# -----------------------------
# Retrieve sensor history
# -----------------------------

@router.get("/readings")
def get_sensor_readings(
    machine_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
):
    with closing(get_connection()) as connection:
        if machine_id:
            rows = connection.execute(
                """
                SELECT *
                FROM sensor_readings
                WHERE machine_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (machine_id, limit),
            ).fetchall()
        else:
            rows = connection.execute(
                """
                SELECT *
                FROM sensor_readings
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

    return {
        "count": len(rows),
        "items": [row_to_dict(row) for row in rows],
    }


# -----------------------------
# Monitoring summary
# -----------------------------

@router.get("/summary")
def get_monitoring_summary():
    with closing(get_connection()) as connection:
        totals = connection.execute(
            """
            SELECT
                COUNT(*) AS total_readings,
                COUNT(DISTINCT machine_id) AS machines_monitored
            FROM sensor_readings
            """
        ).fetchone()

        latest_rows = connection.execute(
            """
            SELECT *
            FROM sensor_readings
            WHERE id IN (
                SELECT MAX(id)
                FROM sensor_readings
                GROUP BY machine_id
            )
            ORDER BY machine_id
            """
        ).fetchall()

    return {
        "total_readings": totals["total_readings"],
        "machines_monitored": totals["machines_monitored"],
        "latest_readings": [
            row_to_dict(row)
            for row in latest_rows
        ],
    }