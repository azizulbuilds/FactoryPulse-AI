from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field


router = APIRouter(
    prefix="/monitoring",
    tags=["Machine Monitoring"],
)


class SensorReading(BaseModel):
    """Sensor measurements from an industrial machine."""

    machine_id: str = Field(
        min_length=1,
        max_length=50,
    )

    air_temperature: float = Field(
        gt=0,
        description="Air temperature in Kelvin",
    )

    process_temperature: float = Field(
        gt=0,
        description="Process temperature in Kelvin",
    )

    rotational_speed: float = Field(
        gt=0,
        description="Rotational speed in RPM",
    )

    torque: float = Field(
        ge=0,
        description="Torque in Nm",
    )

    tool_wear: float = Field(
        ge=0,
        description="Tool wear in minutes",
    )


class MonitoringResponse(BaseModel):
    machine_id: str
    status: Literal["received"]
    received_at: datetime
    sensor_readings: dict[str, float]


@router.post("/readings", response_model=MonitoringResponse)
def receive_sensor_reading(
    reading: SensorReading,
):
    """
    Validate and receive sensor measurements.

    This initial version does not persist readings or
    determine whether a machine is anomalous.
    """

    return MonitoringResponse(
        machine_id=reading.machine_id,
        status="received",
        received_at=datetime.now(timezone.utc),
        sensor_readings={
            "air_temperature": reading.air_temperature,
            "process_temperature": reading.process_temperature,
            "rotational_speed": reading.rotational_speed,
            "torque": reading.torque,
            "tool_wear": reading.tool_wear,
        },
    )