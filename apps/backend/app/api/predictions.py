from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(
    prefix="/predictions",
    tags=["Predictions"],
)


class SensorReading(BaseModel):
    """Sensor readings submitted for anomaly detection."""

    air_temperature_k: float = Field(
        gt=0,
        description="Air temperature in Kelvin",
    )

    process_temperature_k: float = Field(
        gt=0,
        description="Process temperature in Kelvin",
    )

    rotational_speed_rpm: float = Field(
        gt=0,
        description="Machine rotational speed in RPM",
    )

    torque_nm: float = Field(
        ge=0,
        description="Machine torque in Newton-metres",
    )

    tool_wear_min: float = Field(
        ge=0,
        description="Accumulated tool wear in minutes",
    )


@router.post("/anomaly")
def detect_anomaly(reading: SensorReading):
    """
    Assess machine sensor readings using the trained
    anomaly detection model.
    """

    # Convert API field names into dataset column names.
    sensor_readings = {
        "Air temperature [K]": reading.air_temperature_k,
        "Process temperature [K]": reading.process_temperature_k,
        "Rotational speed [rpm]": reading.rotational_speed_rpm,
        "Torque [Nm]": reading.torque_nm,
        "Tool wear [min]": reading.tool_wear_min,
    }

    try:
        # Import the ML code only when a prediction is requested.
        # This allows the backend to run without PyTorch installed.
        from ml.src.predict import (
            load_detector,
            predict_sensor_reading,
        )

        model, scaler, threshold, device = load_detector()

        result = predict_sensor_reading(
            sensor_readings=sensor_readings,
            model=model,
            scaler=scaler,
            threshold=threshold,
            device=device,
        )

        return result

    except ModuleNotFoundError as exc:
        if exc.name == "torch" or exc.name == "joblib":
            raise HTTPException(
                status_code=503,
                detail=(
                    "The ML inference environment is not ready. "
                    "A compatible PyTorch installation and the "
                    "required model artifacts are needed."
                ),
            ) from exc

        raise

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "The anomaly detector is not ready. "
                "The trained model, fitted scaler, and calibrated "
                "anomaly threshold must be available."
            ),
        ) from exc