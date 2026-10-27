from pathlib import Path

from ml.train import train_cell_decoder


def main() -> None:
    path, accuracy = train_cell_decoder()
    print(f"saved {path} held-out accuracy {accuracy:.3f}")


if __name__ == "__main__":
    main()
