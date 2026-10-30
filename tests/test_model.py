from pathlib import Path

import numpy as np
import pytest

from ml.store import load_cell_model
from serialization.decode.errors import DecodeError


@pytest.mark.slow
def test_cell_decoder_output_shape() -> None:
    pytest.importorskip("tensorflow")
    from ml.network import CELL_PX, build_cell_decoder

    model = build_cell_decoder()
    image = np.zeros((1, 4 * CELL_PX, 4 * CELL_PX, 3), np.float32)
    logits, offset = model(image, training=False)
    assert tuple(logits.shape) == (1, 4, 4, 11)
    assert tuple(offset.shape) == (1, 4, 4, 2)


@pytest.mark.slow
def test_saved_model_loads_when_present() -> None:
    pytest.importorskip("tensorflow")
    from ml.store import default_model_path, load_cell_model

    path = default_model_path()
    if not Path(path).is_file():
        pytest.skip("synthetic cell decoder has not been trained")
    assert load_cell_model(path, required=True) is not None


def test_optional_model_is_skipped_without_keras(monkeypatch, tmp_path: Path) -> None:
    model = tmp_path / "cell.keras"
    model.write_bytes(b"not-a-model")
    monkeypatch.setattr("ml.store._import_keras", lambda _required: None)
    assert load_cell_model(model, required=False) is None


def test_keras_import_error_follows_the_required_flag(monkeypatch) -> None:
    from ml.store import _import_keras

    def missing() -> object:
        raise ImportError("tensorflow")

    monkeypatch.setattr("ml.store._load_keras_module", missing)
    assert _import_keras(False) is None
    with pytest.raises(DecodeError, match="TensorFlow is not installed"):
        _import_keras(True)
