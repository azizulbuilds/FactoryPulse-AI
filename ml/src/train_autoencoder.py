import json
from pathlib import Path

import pandas as pd
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from autoencoder import MachineAutoencoder


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

BATCH_SIZE = 128
EPOCHS = 100
LEARNING_RATE = 0.001
PATIENCE = 10
RANDOM_SEED = 42


def load_data():
    """Load the scaled normal training and validation data."""

    train_path = DATA_DIR / "train_normal_scaled.csv"
    validation_path = DATA_DIR / "validation_normal_scaled.csv"

    for path in [train_path, validation_path]:
        if not path.exists():
            raise FileNotFoundError(
                f"Required file not found: {path}"
            )

    train_df = pd.read_csv(train_path)
    validation_df = pd.read_csv(validation_path)

    for name, df in [
        ("training", train_df),
        ("validation", validation_df),
    ]:
        missing = [
            feature for feature in FEATURES
            if feature not in df.columns
        ]

        if missing:
            raise ValueError(
                f"Missing features in {name} data: {missing}"
            )

        if df.empty:
            raise ValueError(f"{name} dataset is empty.")

    train_values = train_df[FEATURES].to_numpy(dtype="float32")
    validation_values = validation_df[FEATURES].to_numpy(
        dtype="float32"
    )

    train_tensor = torch.tensor(train_values)
    validation_tensor = torch.tensor(validation_values)

    if not torch.isfinite(train_tensor).all():
        raise ValueError("Training data contains invalid values.")

    if not torch.isfinite(validation_tensor).all():
        raise ValueError("Validation data contains invalid values.")

    return train_tensor, validation_tensor


def train_autoencoder():
    """Train the anomaly detector on AMD GPU infrastructure."""

    torch.manual_seed(RANDOM_SEED)

    # Refuse to train on the laptop or another CPU-only environment.
    if not torch.cuda.is_available():
        raise RuntimeError(
            "No supported GPU is available to PyTorch. "
            "Training was stopped to avoid accidentally running "
            "the workload on your laptop CPU. Verify that the AMD "
            "GPU and ROCm-enabled PyTorch are configured correctly."
        )

    device = torch.device("cuda:0")

    print(f"Training device: {device}")
    print(f"GPU: {torch.cuda.get_device_name(0)}")

    train_tensor, validation_tensor = load_data()

    train_loader = DataLoader(
        TensorDataset(train_tensor),
        batch_size=BATCH_SIZE,
        shuffle=True,
    )

    validation_loader = DataLoader(
        TensorDataset(validation_tensor),
        batch_size=BATCH_SIZE,
        shuffle=False,
    )

    model = MachineAutoencoder(
        input_dim=len(FEATURES)
    ).to(device)

    criterion = nn.MSELoss()

    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=LEARNING_RATE,
    )

    ARTIFACTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    checkpoint_path = ARTIFACTS_DIR / "autoencoder.pth"

    best_validation_loss = float("inf")
    best_epoch = 0
    epochs_without_improvement = 0

    for epoch in range(1, EPOCHS + 1):

        # Training phase
        model.train()
        train_loss_total = 0.0

        for (batch,) in train_loader:
            batch = batch.to(device)

            optimizer.zero_grad()

            reconstructed = model(batch)
            loss = criterion(reconstructed, batch)

            loss.backward()
            optimizer.step()

            train_loss_total += loss.item() * len(batch)

        train_loss = (
            train_loss_total / len(train_tensor)
        )

        # Validation phase
        model.eval()
        validation_loss_total = 0.0

        with torch.no_grad():
            for (batch,) in validation_loader:
                batch = batch.to(device)

                reconstructed = model(batch)
                loss = criterion(reconstructed, batch)

                validation_loss_total += (
                    loss.item() * len(batch)
                )

        validation_loss = (
            validation_loss_total / len(validation_tensor)
        )

        print(
            f"Epoch {epoch:03d}/{EPOCHS} | "
            f"Train loss: {train_loss:.6f} | "
            f"Validation loss: {validation_loss:.6f}"
        )

        # Save the best model according to validation loss.
        if validation_loss < best_validation_loss - 1e-6:
            best_validation_loss = validation_loss
            best_epoch = epoch
            epochs_without_improvement = 0

            torch.save(
                model.state_dict(),
                checkpoint_path,
            )
        else:
            epochs_without_improvement += 1

        # Early stopping prevents unnecessary training.
        if epochs_without_improvement >= PATIENCE:
            print("\nEarly stopping triggered.")
            break

    metadata = {
        "model": "MachineAutoencoder",
        "features": FEATURES,
        "best_epoch": best_epoch,
        "best_validation_loss": best_validation_loss,
        "batch_size": BATCH_SIZE,
        "learning_rate": LEARNING_RATE,
        "seed": RANDOM_SEED,
        "device": str(device),
        "gpu_name": torch.cuda.get_device_name(0),
    }

    metadata_path = ARTIFACTS_DIR / "training_metadata.json"

    with open(metadata_path, "w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=4)

    print("\nTRAINING COMPLETE")
    print(f"Best epoch: {best_epoch}")
    print(f"Best validation loss: {best_validation_loss:.6f}")
    print(f"Model saved to: {checkpoint_path}")
    print(f"Metadata saved to: {metadata_path}")


if __name__ == "__main__":
    train_autoencoder()