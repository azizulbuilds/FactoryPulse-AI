import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import torch

if __package__:
    from .autoencoder import MachineAutoencoder
else:
    from autoencoder import MachineAutoencoder

# --------------------------------------------------
# Configuration
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

ARTIFACTS_DIR = PROJECT_ROOT / "ml" / "artifacts"

MODEL_PATH = ARTIFACTS_DIR / "autoencoder.pth"
SCALER_PATH = ARTIFACTS_DIR / "scaler.joblib"
THRESHOLD_PATH = ARTIFACTS_DIR / "anomaly_threshold.json"

FEATURES = [
    "Air temperature [K]",
    "Process temperature [K]",
    "Rotational speed [rpm]",
    "Torque [Nm]",
    "Tool wear [min]",
]


# --------------------------------------------------
# Load the trained detector
# --------------------------------------------------

def load_detector():
    """
    Load the trained autoencoder, feature scaler,
    anomaly threshold, and inference device.
    """

    required_files = [
        MODEL_PATH,
        SCALER_PATH,
        THRESHOLD_PATH,
    ]

    for path in required_files:
        if not path.exists():
            raise FileNotFoundError(
                f"Required artifact not found: {path}"
            )

    # PyTorch uses the CUDA API for supported ROCm GPUs too.
    # CPU is also permitted for inference when no GPU is available.
    device = torch.device(
        "cuda:0" if torch.cuda.is_available() else "cpu"
    )

    model = MachineAutoencoder(
        input_dim=len(FEATURES)
    ).to(device)

    state_dict = torch.load(
        MODEL_PATH,
        map_location=device,
        weights_only=True,
    )

    model.load_state_dict(state_dict)
    model.eval()

    scaler = joblib.load(SCALER_PATH)

    with open(
        THRESHOLD_PATH,
        "r",
        encoding="utf-8",
    ) as file:
        threshold_config = json.load(file)

    threshold = float(threshold_config["threshold"])

    if not np.isfinite(threshold) or threshold < 0:
        raise ValueError(
            "The anomaly threshold must be a finite, "
            "non-negative number."
        )

    print(f"Detector loaded on: {device}")

    if device.type == "cuda":
        print(f"GPU: {torch.cuda.get_device_name(0)}")

    return model, scaler, threshold, device


# --------------------------------------------------
# Predict one machine reading
# --------------------------------------------------

def predict_sensor_reading(
    sensor_readings: dict[str, Any],
    model,
    scaler,
    threshold: float,
    device: torch.device,
) -> dict[str, Any]:
    """
    Calculate a reconstruction-error anomaly score
    for one machine sensor reading.
    """

    # Verify that every required sensor feature exists.
    missing_features = [
        feature
        for feature in FEATURES
        if feature not in sensor_readings
    ]

    if missing_features:
        raise ValueError(
            f"Missing sensor features: {missing_features}"
        )

    # Preserve the exact feature ordering used during training.
    try:
        values = np.asarray(
            [
                float(sensor_readings[feature])
                for feature in FEATURES
            ],
            dtype=np.float32,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "Every sensor reading must be numeric."
        ) from exc

    if not np.isfinite(values).all():
        raise ValueError(
            "Sensor readings must be finite numbers."
        )

    if not np.isfinite(threshold) or threshold < 0:
        raise ValueError("Invalid anomaly threshold.")

    # Apply the scaler fitted on normal training data.
    scaled_values = scaler.transform(
        values.reshape(1, -1)
    )

    tensor = torch.tensor(
        scaled_values,
        dtype=torch.float32,
        device=device,
    )

    # Generate the reconstruction and calculate its error.
    model.eval()

    with torch.inference_mode():
        reconstructed = model(tensor)

        anomaly_score = torch.mean(
            (tensor - reconstructed) ** 2,
            dim=1,
        ).item()

    # Compare the error with the calibrated threshold.
    is_anomaly = anomaly_score > threshold

    return {
        "anomaly_score": round(float(anomaly_score), 6),
        "threshold": round(float(threshold), 6),
        "is_anomaly": bool(is_anomaly),
        "status": (
            "ANOMALY" if is_anomaly else "NORMAL"
        ),
        "model": "MachineAutoencoder",
    }