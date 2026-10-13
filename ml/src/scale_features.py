from pathlib import Path

import joblib
import pandas as pd
from sklearn.preprocessing import StandardScaler


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "ml" / "data" / "processed"
ARTIFACTS_DIR = PROJECT_ROOT / "ml" / "artifacts"

FEATURES = [
    "Air temperature [K]",
    "Process temperature [K]",
    "Rotational speed [rpm]",
    "Torque [Nm]",
    "Tool wear [min]",
]


def scale_features() -> None:
    """Scale sensor features without evaluation data leakage."""

    train_path = DATA_DIR / "train_normal.csv"
    validation_path = DATA_DIR / "validation_normal.csv"
    evaluation_path = DATA_DIR / "test_evaluation.csv"

    required_files = [
        train_path,
        validation_path,
        evaluation_path,
    ]

    for path in required_files:
        if not path.exists():
            raise FileNotFoundError(
                f"Required dataset not found: {path}"
            )

    # Load the datasets.
    train_df = pd.read_csv(train_path)
    validation_df = pd.read_csv(validation_path)
    evaluation_df = pd.read_csv(evaluation_path)

    # Validate that the required sensor features exist.
    for name, df in [
        ("training", train_df),
        ("validation", validation_df),
        ("evaluation", evaluation_df),
    ]:
        missing = [
            feature for feature in FEATURES
            if feature not in df.columns
        ]

        if missing:
            raise ValueError(
                f"Missing features in {name} data: {missing}"
            )

    # Fit ONLY on normal training records.
    scaler = StandardScaler()
    scaler.fit(train_df[FEATURES])

    # Transform all datasets using the same scaler.
    train_scaled = train_df.copy()
    validation_scaled = validation_df.copy()
    evaluation_scaled = evaluation_df.copy()

    train_scaled[FEATURES] = scaler.transform(
        train_df[FEATURES]
    )

    validation_scaled[FEATURES] = scaler.transform(
        validation_df[FEATURES]
    )

    evaluation_scaled[FEATURES] = scaler.transform(
        evaluation_df[FEATURES]
    )

    # Create output directories.
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    # Save scaled datasets.
    train_scaled.to_csv(
        DATA_DIR / "train_normal_scaled.csv",
        index=False,
    )

    validation_scaled.to_csv(
        DATA_DIR / "validation_normal_scaled.csv",
        index=False,
    )

    evaluation_scaled.to_csv(
        DATA_DIR / "test_evaluation_scaled.csv",
        index=False,
    )

    # Save the fitted scaler for later inference.
    joblib.dump(
        scaler,
        ARTIFACTS_DIR / "scaler.joblib",
    )

    # Verify training feature statistics.
    print("\n" + "=" * 55)
    print("FORGEPULSE AI — FEATURE SCALING")
    print("=" * 55)

    print("\nScaled dataset shapes:")
    print(f"Training:    {train_scaled.shape}")
    print(f"Validation:  {validation_scaled.shape}")
    print(f"Evaluation:  {evaluation_scaled.shape}")

    print("\nTraining feature means (approximately zero):")
    print(
        train_scaled[FEATURES]
        .mean()
        .round(4)
        .to_string()
    )

    print("\nTraining feature standard deviations:")
    print(
        train_scaled[FEATURES]
        .std(ddof=0)
        .round(4)
        .to_string()
    )

    print("\nSaved artifacts:")
    print("- ml/artifacts/scaler.joblib")
    print("- ml/data/processed/train_normal_scaled.csv")
    print("- ml/data/processed/validation_normal_scaled.csv")
    print("- ml/data/processed/test_evaluation_scaled.csv")

    print("\nFEATURE SCALING COMPLETE")


if __name__ == "__main__":
    scale_features()