import logging
import os
from pathlib import Path

from serialization.decode.errors import DecodeError

logger = logging.getLogger(__name__)

_DEFAULT = Path(__file__).resolve().parents[2] / "models" / "cell_decoder.keras"


def default_model_path() -> Path:
    return _DEFAULT


def load_cell_model(path: Path | None = None, required: bool = False) -> object | None:
    target = path if path is not None else _DEFAULT
    if not target.is_file():
        if required:
            raise DecodeError(f"cell decoder model not found: {target}")
        return None
    keras = _import_keras(required)
    if keras is None:
        return None
    return keras.models.load_model(target, compile=False)


def _import_keras(required: bool) -> object | None:
    os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
    try:
        return _load_keras_module()
    except ImportError as exc:
        if required:
            raise DecodeError("TensorFlow is not installed on this platform") from exc
        logger.warning("TensorFlow is not installed; skipping the cell decoder")
        return None


def _load_keras_module() -> object:
    from tensorflow import keras

    return keras
