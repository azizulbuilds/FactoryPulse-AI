import torch
from torch import nn


class MachineAutoencoder(nn.Module):
    """
    Autoencoder for five industrial sensor features.

    Input:  5 sensor values
    Latent: 2 compressed features
    Output: 5 reconstructed sensor values
    """

    def __init__(self, input_dim: int = 5):
        super().__init__()

        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 8),
            nn.ReLU(),
            nn.Linear(8, 4),
            nn.ReLU(),
            nn.Linear(4, 2),
        )

        self.decoder = nn.Sequential(
            nn.Linear(2, 4),
            nn.ReLU(),
            nn.Linear(4, 8),
            nn.ReLU(),
            nn.Linear(8, input_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        encoded = self.encoder(x)
        reconstructed = self.decoder(encoded)

        return reconstructed