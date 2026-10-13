from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_PATH = (
    PROJECT_ROOT
    / "ml"
    / "data"
    / "processed"
    / "sensor_data.csv"
)

OUTPUT_DIR = PROJECT_ROOT / "ml" / "data" / "processed"

FEATURES = [
    "Air temperature [K]",
    "Process temperature [K]",
    "Rotational speed [rpm]",
    "Torque [Nm]",
    "Tool wear [min]",
]

TARGET = "Machine failure"

RANDOM_STATE = 42


def split_dataset() -> None:
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Processed dataset not found: {DATA_PATH}"
        )

    df = pd.read_csv(DATA_PATH)

    normal = df[df[TARGET] == 0].copy()
    failures = df[df[TARGET] == 1].copy()

    # Reserve failure records for final evaluation.
    # Do not use these records to fit the anomaly detector.
    normal_train, normal_remaining = train_test_split(
        normal,
        test_size=0.30,
        random_state=RANDOM_STATE,
        shuffle=True,
    )

    normal_validation, normal_test = train_test_split(
        normal_remaining,
        test_size=0.50,
        random_state=RANDOM_STATE,
        shuffle=True,
    )

    # Evaluation set contains all held-out normal records
    # and all known failure records.
    evaluation = pd.concat(
        [normal_test, failures],
        ignore_index=True,
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    normal_train[FEATURES].to_csv(
        OUTPUT_DIR / "train_normal.csv",
        index=False,
    )

    normal_validation[FEATURES].to_csv(
        OUTPUT_DIR / "validation_normal.csv",
        index=False,
    )

    evaluation[FEATURES + [TARGET]].to_csv(
        OUTPUT_DIR / "test_evaluation.csv",
        index=False,
    )

    print("\n" + "=" * 55)
    print("FORGEPULSE AI — DATA SPLITTING")
    print("=" * 55)

    print(f"\nNormal training records: {len(normal_train)}")
    print(f"Normal validation records: {len(normal_validation)}")
    print(f"Normal test records: {len(normal_test)}")
    print(f"Failure evaluation records: {len(failures)}")
    print(f"Total evaluation records: {len(evaluation)}")

    print("\nEvaluation label distribution:")
    print(
        evaluation[TARGET]
        .value_counts()
        .sort_index()
        .rename(index={0: "Normal", 1: "Failure"})
        .to_string()
    )

    print("\nCreated files:")
    print("- train_normal.csv")
    print("- validation_normal.csv")
    print("- test_evaluation.csv")

    print("\nDATA SPLITTING COMPLETE")


if __name__ == "__main__":
    split_dataset()