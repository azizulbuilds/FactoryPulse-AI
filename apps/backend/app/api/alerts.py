import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field


router = APIRouter(
    prefix="/alerts",
    tags=["Machine Alerts"],
)


# --------------------------------------------------
# Database configuration
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[4]

DATABASE_PATH = (
    PROJECT_ROOT
    / "apps"
    / "backend"
    / "data"
    / "factorypulse.db"
)


def get_connection() -> sqlite3.Connection:
    """Create a database connection."""

    DATABASE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    return connection


def initialize_database() -> None:
    """Create the alerts table if it doesn't exist."""

    with get_connection() as connection:
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
                created_at TEXT NOT NULL,
                acknowledged_at TEXT
            )
            """
        )


# --------------------------------------------------
# Request models
# --------------------------------------------------

class AlertCreateRequest(BaseModel):
    """Information required to create an alert."""

    machine_id: str = Field(
        min_length=1,
        max_length=50,
    )

    severity: Literal[
        "info",
        "warning",
        "critical",
    ]

    title: str = Field(
        min_length=3,
        max_length=150,
    )

    message: str = Field(
        min_length=3,
        max_length=1000,
    )

    anomaly_score: float | None = Field(
        default=None,
        ge=0,
        allow_inf_nan=False,
    )

    threshold: float | None = Field(
        default=None,
        ge=0,
        allow_inf_nan=False,
    )


# --------------------------------------------------
# Create an alert
# --------------------------------------------------

@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
)
def create_alert(request: AlertCreateRequest):
    """Create and persist a machine alert."""

    initialize_database()

    created_at = datetime.now(
        timezone.utc
    ).isoformat()

    with get_connection() as connection:
        cursor = connection.execute(
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
                request.machine_id,
                request.severity,
                request.title,
                request.message,
                request.anomaly_score,
                request.threshold,
                "open",
                created_at,
            ),
        )

        alert_id = cursor.lastrowid

        row = connection.execute(
            "SELECT * FROM alerts WHERE id = ?",
            (alert_id,),
        ).fetchone()

    return dict(row)


# --------------------------------------------------
# List alerts
# --------------------------------------------------

@router.get("")
def list_alerts(
    machine_id: str | None = Query(
        default=None,
        max_length=50,
    ),
    alert_status: Literal[
        "open",
        "acknowledged",
    ] | None = Query(
        default=None,
        alias="status",
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
    ),
):
    """List alerts with optional filtering."""

    initialize_database()

    conditions = []
    parameters = []

    if machine_id:
        conditions.append("machine_id = ?")
        parameters.append(machine_id)

    if alert_status:
        conditions.append("status = ?")
        parameters.append(alert_status)

    sql = "SELECT * FROM alerts"

    if conditions:
        sql += " WHERE " + " AND ".join(conditions)

    sql += " ORDER BY id DESC LIMIT ?"
    parameters.append(limit)

    with get_connection() as connection:
        rows = connection.execute(
            sql,
            parameters,
        ).fetchall()

    alerts = [dict(row) for row in rows]

    return {
        "total": len(alerts),
        "alerts": alerts,
    }


# --------------------------------------------------
# Get one alert
# --------------------------------------------------

@router.get("/{alert_id}")
def get_alert(alert_id: int):
    """Return details for a specific alert."""

    initialize_database()

    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM alerts WHERE id = ?",
            (alert_id,),
        ).fetchone()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Alert not found.",
        )

    return dict(row)


# --------------------------------------------------
# Acknowledge an alert
# --------------------------------------------------

@router.patch("/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: int):
    """Mark an open alert as acknowledged."""

    initialize_database()

    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM alerts WHERE id = ?",
            (alert_id,),
        ).fetchone()

        if row is None:
            raise HTTPException(
                status_code=404,
                detail="Alert not found.",
            )

        if row["status"] == "open":
            acknowledged_at = datetime.now(
                timezone.utc
            ).isoformat()

            connection.execute(
                """
                UPDATE alerts
                SET status = ?, acknowledged_at = ?
                WHERE id = ?
                """,
                (
                    "acknowledged",
                    acknowledged_at,
                    alert_id,
                ),
            )

        updated_row = connection.execute(
            "SELECT * FROM alerts WHERE id = ?",
            (alert_id,),
        ).fetchone()

    return dict(updated_row)