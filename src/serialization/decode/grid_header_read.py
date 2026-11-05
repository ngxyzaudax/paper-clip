import numpy as np

from common.config import PaperClipConfig
from common.geometry import PageGeometry
from common.header_cells import split_cells
from common.header_grid import header_grid_byte_count
from serialization.decode.classify import classify_cells
from serialization.decode.erasures import bytes_and_erasures
from serialization.decode.grid_codec import header_from_grid_bytes
from serialization.encode.header_bytes import DecodedQrHeader


def read_grid_header(
    warped: np.ndarray,
    geometry: PageGeometry,
    config: PaperClipConfig,
    dx: int,
    dy: int,
    refs: np.ndarray,
    model: object | None,
    colour: np.ndarray,
) -> DecodedQrHeader | None:
    cells, _data = split_cells(config)
    if not cells:
        return None
    symbols, confidence = classify_cells(
        warped, geometry, config, dx, dy, refs, model, cells, colour,
    )
    blob, erasures = bytes_and_erasures(symbols, confidence, config.num_symbols, header_grid_byte_count())
    return header_from_grid_bytes(blob, erasures)
