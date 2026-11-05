import numpy as np
import pytest

from serialization.decode.model_strips import CELL_PX, HALO, STRIP_ROWS, groups, strips


def test_strips_keep_a_two_cell_halo_around_each_block() -> None:
    tiles = strips(130)
    assert len(tiles) == 3
    assert tiles[0].row0 == 0 and tiles[0].row1 == STRIP_ROWS
    assert tiles[0].y0 == 0
    assert tiles[1].y0 == (STRIP_ROWS - HALO) * CELL_PX
    assert tiles[2].row0 == 128 and tiles[2].row1 == 130
    assert tiles[2].y1 == 130 * CELL_PX
    heights = [item.y1 - item.y0 for item in tiles]
    assert len(groups(tiles)) == len(set(heights))


@pytest.mark.slow
def test_batched_strips_match_a_full_forward() -> None:
    pytest.importorskip("tensorflow")
    from ml.network import build_cell_decoder
    from serialization.decode.model_batch import forward_grid

    rng = np.random.default_rng(0)
    rows, cols = 200, 8
    image = rng.random((rows * CELL_PX, cols * CELL_PX, 3)).astype(np.float32)
    model = build_cell_decoder()
    logits, offset = forward_grid(model, image)
    full_logits, full_offset = model(image[None], training=False)
    np.testing.assert_allclose(logits, np.asarray(full_logits)[0], atol=1e-5)
    np.testing.assert_allclose(offset, np.asarray(full_offset)[0], atol=1e-5)
