from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DATA_PATH = (
    PROJECT_ROOT / "ml" / "data" / "raw" / "ai4i2020.csv"
)

OUTPUT_DIR = PROJECT_ROOT / "ml" / "data" / "processed"

SENSOR_FEATURES = [
    "Air temperature [K]",
    "Process temperature [K]",
    "Rotational speed [rpm]",
    "Torque [Nm]",
    "Tool wear [min]",
]

TARGET_COLUMN = "Machine failure"


def prepare_dataset() -> None:
    """Validate sensor data and save model-ready features."""

    if not RAW_DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {RAW_DATA_PATH}"
        )

    df = pd.read_csv(RAW_DATA_PATH)

    required_columns = SENSOR_FEATURES + [TARGET_COLUMN]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Required columns missing: {missing_columns}"
        )

    # Keep only sensor features and the evaluation label.
    data = df[required_columns].copy()

    # Ensure sensor readings are numeric.
    data[SENSOR_FEATURES] = data[
        SENSOR_FEATURES
    ].apply(pd.to_numeric, errors="raise")

    # Validate labels.
    if data[TARGET_COLUMN].isna().any():
        raise ValueError("Machine failure labels contain missing values.")

    if not data[TARGET_COLUMN].isin([0, 1]).all():
        raise ValueError("Unexpected values in Machine failure labels.")

    # Remove incomplete sensor records if present.
    original_rows = len(data)

    data = data.dropna(subset=SENSOR_FEATURES)

    removed_rows = original_rows - len(data)

    # Save the processed dataset.
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    output_path = OUTPUT_DIR / "sensor_data.csv"

    data.to_csv(output_path, index=False)

    # Report results.
    print("\n" + "=" * 50)
    print("FORGEPULSE AI — DATA PREPARATION")
    print("=" * 50)

    print(f"\nOriginal rows: {original_rows}")
    print(f"Rows removed: {removed_rows}")
    print(f"Rows retained: {len(data)}")

    print("\nSensor features:")
    for feature in SENSOR_FEATURES:
        print(f"- {feature}")

    print("\nMachine failure distribution:")
    print(
        data[TARGET_COLUMN]
        .value_counts()
        .sort_index()
        .rename(index={0: "Normal", 1: "Failure"})
        .to_string()
    )

    print(f"\nSaved processed data to:\n{output_path}")

    print("\nDATA PREPARATION COMPLETE")


if __name__ == "__main__":
    prepare_dataset()