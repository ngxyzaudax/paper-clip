from pathlib import Path

import numpy as np
import pytest


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
