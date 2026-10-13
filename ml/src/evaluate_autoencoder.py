import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from autoencoder import MachineAutoencoder


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "ml" / "data" / "processed"
ARTIFACTS_DIR = PROJECT_ROOT / "ml" / "artifacts"

VALIDATION_FILE = DATA_DIR / "validation_normal_scaled.csv"
EVALUATION_FILE = DATA_DIR / "test_evaluation_scaled.csv"
MODEL_FILE = ARTIFACTS_DIR / "autoencoder.pth"

FEATURES = [
    "Air temperature [K]",
    "Process temperature [K]",
    "Rotational speed [rpm]",
    "Torque [Nm]",
    "Tool wear [min]",
]

TARGET = "Machine failure"

THRESHOLD_PERCENTILE = 95


def load_csv(path: Path, required_columns: list[str]) -> pd.DataFrame:
    """Load a CSV and validate the required columns."""

    if not path.exists():
        raise FileNotFoundError(
            f"Required file not found: {path}"
        )

    df = pd.read_csv(path)

    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing columns in {path.name}: {missing}"
        )

    if df.empty:
        raise ValueError(f"{path.name} is empty.")

    return df


def calculate_reconstruction_errors(
    model: MachineAutoencoder,
    values: np.ndarray,
    device: torch.device,
) -> np.ndarray:
    """Calculate mean squared reconstruction error per record."""

    tensor = torch.tensor(
        values,
        dtype=torch.float32,
        device=device,
    )

    model.eval()

    with torch.inference_mode():
        reconstructed = model(tensor)

        errors = torch.mean(
            (tensor - reconstructed) ** 2,
            dim=1,
        )

    return errors.cpu().numpy()


def evaluate_model() -> None:
    """Evaluate the trained anomaly detector."""

    if not torch.cuda.is_available():
        raise RuntimeError(
            "A compatible GPU is required for this evaluation. "
            "Run this script in the configured AMD cloud "
            "environment with ROCm-enabled PyTorch."
        )

    if not MODEL_FILE.exists():
        raise FileNotFoundError(
            f"Trained model not found: {MODEL_FILE}\n"
            "Train the autoencoder on the AMD cloud first."
        )

    device = torch.device("cuda:0")

    print(f"Evaluation device: {device}")
    print(f"GPU: {torch.cuda.get_device_name(0)}")

    # Load normal validation and held-out evaluation data.
    validation_df = load_csv(
        VALIDATION_FILE,
        FEATURES,
    )

    evaluation_df = load_csv(
        EVALUATION_FILE,
        FEATURES + [TARGET],
    )

    # Convert sensor readings to numeric arrays.
    validation_values = validation_df[
        FEATURES
    ].to_numpy(dtype=np.float32)

    evaluation_values = evaluation_df[
        FEATURES
    ].to_numpy(dtype=np.float32)

    labels = evaluation_df[TARGET].to_numpy(dtype=int)

    if not np.isfinite(validation_values).all():
        raise ValueError(
            "Validation data contains invalid numeric values."
        )

    if not np.isfinite(evaluation_values).all():
        raise ValueError(
            "Evaluation data contains invalid numeric values."
        )

    if not np.isin(labels, [0, 1]).all():
        raise ValueError(
            "Evaluation labels must contain only 0 and 1."
        )

    # Load the trained model checkpoint.
    model = MachineAutoencoder(
        input_dim=len(FEATURES)
    ).to(device)

    state_dict = torch.load(
        MODEL_FILE,
        map_location=device,
    )

    model.load_state_dict(state_dict)
    model.eval()

    # Establish a threshold from normal validation data only.
    validation_errors = calculate_reconstruction_errors(
        model,
        validation_values,
        device,
    )

    threshold = float(
        np.percentile(
            validation_errors,
            THRESHOLD_PERCENTILE,
        )
    )

    # Evaluate the held-out dataset.
    evaluation_errors = calculate_reconstruction_errors(
        model,
        evaluation_values,
        device,
    )

    predictions = (
        evaluation_errors > threshold
    ).astype(int)

    # Calculate classification metrics.
    accuracy = accuracy_score(labels, predictions)

    precision = precision_score(
        labels,
        predictions,
        zero_division=0,
    )

    recall = recall_score(
        labels,
        predictions,
        zero_division=0,
    )

    f1 = f1_score(
        labels,
        predictions,
        zero_division=0,
    )

    pr_auc = average_precision_score(
        labels,
        evaluation_errors,
    )

    roc_auc = roc_auc_score(
        labels,
        evaluation_errors,
    )

    tn, fp, fn, tp = confusion_matrix(
        labels,
        predictions,
        labels=[0, 1],
    ).ravel()

    # Save record-level predictions.
    results_df = evaluation_df.copy()

    results_df["anomaly_score"] = evaluation_errors
    results_df["predicted_anomaly"] = predictions

    ARTIFACTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    predictions_path = (
        ARTIFACTS_DIR / "evaluation_predictions.csv"
    )

    results_df.to_csv(
        predictions_path,
        index=False,
    )

    # Save threshold and evaluation metrics.
    metrics = {
        "evaluation_device": str(device),
        "gpu_name": torch.cuda.get_device_name(0),
        "threshold_percentile": THRESHOLD_PERCENTILE,
        "anomaly_threshold": threshold,
        "evaluation_records": int(len(labels)),
        "known_failures": int(np.sum(labels == 1)),
        "known_normal_records": int(np.sum(labels == 0)),
        "accuracy": float(accuracy),
        "precision": float(precision),
        "recall": float(recall),
        "f1_score": float(f1),
        "pr_auc_average_precision": float(pr_auc),
        "roc_auc": float(roc_auc),
        "true_negatives": int(tn),
        "false_positives": int(fp),
        "false_negatives": int(fn),
        "true_positives": int(tp),
    }

    metrics_path = (
        ARTIFACTS_DIR / "evaluation_metrics.json"
    )

    with open(
        metrics_path,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(metrics, file, indent=4)

    threshold_path = (
        ARTIFACTS_DIR / "anomaly_threshold.json"
    )

    with open(
        threshold_path,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            {
                "method": "normal_validation_percentile",
                "percentile": THRESHOLD_PERCENTILE,
                "threshold": threshold,
            },
            file,
            indent=4,
        )

    # Display results.
    print("\n" + "=" * 60)
    print("FORGEPULSE AI — MODEL EVALUATION")
    print("=" * 60)

    print(f"\nEvaluation records: {len(labels)}")
    print(f"Threshold: {threshold:.6f}")

    print("\nClassification metrics:")
    print(f"Accuracy:  {accuracy:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall:    {recall:.4f}")
    print(f"F1-score:  {f1:.4f}")
    print(f"PR-AUC:    {pr_auc:.4f}")
    print(f"ROC-AUC:   {roc_auc:.4f}")

    print("\nConfusion matrix:")
    print(f"True negatives:  {tn}")
    print(f"False positives: {fp}")
    print(f"False negatives: {fn}")
    print(f"True positives:  {tp}")

    print("\nSaved results:")
    print(f"- {predictions_path}")
    print(f"- {metrics_path}")
    print(f"- {threshold_path}")

    print("\nMODEL EVALUATION COMPLETE")


if __name__ == "__main__":
    evaluate_model()