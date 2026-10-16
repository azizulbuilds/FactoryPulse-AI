from contextlib import closing

from fastapi import APIRouter, HTTPException, Query

from app.api.monitoring import get_connection
from app.services.machine_health import calculate_machine_health


router = APIRouter(
    prefix="/machine-health",
    tags=["Machine Health"],
)


@router.get("/{machine_id}")
def get_machine_health(
    machine_id: str,
):
    """
    Calculate the health score using the machine's latest
    stored sensor reading.
    """

    with closing(get_connection()) as connection:
        row = connection.execute(
            """
            SELECT
                machine_id,
                air_temperature,
                process_temperature,
                rotational_speed,
                torque,
                tool_wear,
                received_at
            FROM sensor_readings
            WHERE machine_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (machine_id,),
        ).fetchone()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail=f"No sensor readings found for machine '{machine_id}'.",
        )

    reading = dict(row)

    result = calculate_machine_health(reading)

    result["latest_reading"] = {
        "air_temperature": reading["air_temperature"],
        "process_temperature": reading["process_temperature"],
        "rotational_speed": reading["rotational_speed"],
        "torque": reading["torque"],
        "tool_wear": reading["tool_wear"],
        "received_at": reading["received_at"],
    }

    return result


@router.get("/")
def get_health_endpoint_info():
    """Describe how to use the machine health endpoint."""

    return {
        "feature": "Machine Health Scoring",
        "method": "GET",
        "usage": "/api/v1/machine-health/{machine_id}",
        "scoring_method": "rule_based",
        "description": (
            "Calculates a demonstration health score from "
            "the latest stored sensor reading."
        ),
    }