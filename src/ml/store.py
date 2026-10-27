from pathlib import Path

from serialization.decode.errors import DecodeError

_DEFAULT = Path(__file__).resolve().parents[2] / "models" / "cell_decoder.keras"


def default_model_path() -> Path:
    return _DEFAULT


def load_cell_model(path: Path | None = None, required: bool = False):
    target = path if path is not None else _DEFAULT
    if not target.is_file():
        if required:
            raise DecodeError(f"cell decoder model not found: {target}")
        return None
    import os

    os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
    from tensorflow import keras

    return keras.models.load_model(target, compile=False)
