import numpy as np

from common.page_layout import valid_cells_ordered
from serialization.decode.header_config import config_from_header
from serialization.encode.qr_header import DecodedQrHeader


def page_cell_grid(header: DecodedQrHeader) -> np.ndarray:
    """Row and column of every data cell, in the order symbols are written on the page."""
    return np.asarray(valid_cells_ordered(config_from_header(header)), np.int64).reshape(-1, 2)
