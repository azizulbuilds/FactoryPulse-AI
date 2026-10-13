from pathlib import Path

import pandas as pd


# Resolve the project root from this script's location.
PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_PATH = (
    PROJECT_ROOT
    / "ml"
    / "data"
    / "raw"
    / "ai4i2020.csv"
)


def inspect_dataset() -> None:
    """Inspect the dataset's structure and failure labels."""

    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found at: {DATA_PATH}\n"
            "Ensure ai4i2020.csv is inside ml/data/raw/."
        )

    df = pd.read_csv(DATA_PATH)

    print("\n" + "=" * 60)
    print("FORGEPULSE AI — DATASET INSPECTION")
    print("=" * 60)

    # 1. Dataset dimensions
    print("\n1. DATASET SHAPE")
    print(f"Rows: {df.shape[0]}")
    print(f"Columns: {df.shape[1]}")

    # 2. Column names
    print("\n2. COLUMN NAMES")
    for column in df.columns:
        print(f"- {column}")

    # 3. Data types
    print("\n3. DATA TYPES")
    print(df.dtypes.to_string())

    # 4. Missing values
    print("\n4. MISSING VALUES")
    missing = df.isnull().sum()
    print(missing.to_string())

    if missing.sum() == 0:
        print("\nNo missing values found.")

    # 5. First five records
    print("\n5. FIRST FIVE RECORDS")
    print(df.head().to_string(index=False))

    # 6. Machine failure distribution
    target_column = "Machine failure"

    print("\n6. MACHINE FAILURE DISTRIBUTION")

    if target_column in df.columns:
        counts = df[target_column].value_counts().sort_index()
        percentages = (
            df[target_column]
            .value_counts(normalize=True)
            .sort_index()
            .mul(100)
        )

        for label in counts.index:
            description = (
                "Failure" if label == 1 else "No failure"
                if label == 0
                else "Other label"
            )

            print(
                f"{description} (label={label}): "
                f"{counts[label]} records "
                f"({percentages[label]:.2f}%)"
            )
    else:
        print(f"Column '{target_column}' was not found.")

    # 7. Summary statistics
    print("\n7. NUMERICAL SUMMARY")
    print(df.describe().to_string())

    print("\n" + "=" * 60)
    print("DATASET INSPECTION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    inspect_dataset()