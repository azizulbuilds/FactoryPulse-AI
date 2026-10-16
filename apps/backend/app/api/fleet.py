from contextlib import closing

from fastapi import APIRouter

from app.api.monitoring import get_connection
from app.services.machine_health import calculate_machine_health


router = APIRouter(
    prefix="/fleet",
    tags=["Machine Fleet"],
)


@router.get("/overview")
def get_fleet_overview():
    """
    Return a dashboard-ready summary of all monitored machines.
    """

    with closing(get_connection()) as connection:

        # Get the latest sensor reading for every machine.
        latest_readings = connection.execute(
            """
            SELECT s.*
            FROM sensor_readings AS s
            INNER JOIN (
                SELECT machine_id, MAX(id) AS latest_id
                FROM sensor_readings
                GROUP BY machine_id
            ) AS latest
            ON s.id = latest.latest_id
            ORDER BY s.machine_id
            """
        ).fetchall()

        # Count open alerts for every machine.
        open_alert_rows = connection.execute(
            """
            SELECT machine_id, COUNT(*) AS open_alerts
            FROM alerts
            WHERE status = 'open'
            GROUP BY machine_id
            """
        ).fetchall()

    open_alert_counts = {
        row["machine_id"]: row["open_alerts"]
        for row in open_alert_rows
    }

    machines = []

    for row in latest_readings:
        reading = dict(row)

        health = calculate_machine_health(reading)

        machines.append(
            {
                "machine_id": reading["machine_id"],
                "health_score": health["health_score"],
                "condition": health["condition"],
                "reasons": health["reasons"],
                "open_alerts": open_alert_counts.get(
                    reading["machine_id"],
                    0,
                ),
                "latest_reading_at": reading["received_at"],
                "sensor_readings": {
                    "air_temperature": reading["air_temperature"],
                    "process_temperature": reading["process_temperature"],
                    "rotational_speed": reading["rotational_speed"],
                    "torque": reading["torque"],
                    "tool_wear": reading["tool_wear"],
                },
            }
        )

    total_machines = len(machines)

    healthy_machines = sum(
        machine["condition"] == "healthy"
        for machine in machines
    )

    attention_required = sum(
        machine["condition"] == "attention_required"
        for machine in machines
    )

    critical_machines = sum(
        machine["condition"] == "critical"
        for machine in machines
    )

    total_open_alerts = sum(open_alert_counts.values())

    average_health = (
        round(
            sum(machine["health_score"] for machine in machines)
            / total_machines,
            1,
        )
        if total_machines
        else None
    )

    return {
        "summary": {
            "total_machines": total_machines,
            "healthy_machines": healthy_machines,
            "attention_required": attention_required,
            "critical_machines": critical_machines,
            "total_open_alerts": total_open_alerts,
            "average_health_score": average_health,
        },
        "machines": machines,
        "scoring_method": "rule_based",
    }