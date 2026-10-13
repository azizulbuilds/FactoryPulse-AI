import torch

from autoencoder import MachineAutoencoder


def main():
    model = MachineAutoencoder()

    # Four example records, each with five sensor features.
    sample_input = torch.randn(4, 5)

    reconstructed = model(sample_input)

    print("Input shape:", tuple(sample_input.shape))
    print("Output shape:", tuple(reconstructed.shape))

    assert reconstructed.shape == sample_input.shape

    print("Autoencoder architecture test passed!")


if __name__ == "__main__":
    main()