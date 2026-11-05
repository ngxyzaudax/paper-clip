import numpy as np

from common.geometry_types import PageGeometry
from serialization.decode.grid_align import align_grid


def test_align_grid_pulls_a_raised_dot_back_into_its_cell() -> None:
    geometry = _geometry()
    image = np.full((40, 40, 3), 255, np.uint8)
    image[5:15, 10:20] = (0, 0, 0)
    offset = np.zeros((4, 4, 2), np.float32)
    offset[:, :, 1] = -0.3
    aligned = align_grid(image, geometry, offset)
    assert int(aligned[15, 15, 0]) < 128
    assert int(image[15, 15, 0]) == 255


def _geometry() -> PageGeometry:
    return PageGeometry(
        40, 40, 0, 0, 40, 40, 10, 4, 4, (), 0, (), 0, 0, (),
    )
