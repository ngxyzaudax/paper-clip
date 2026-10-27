from pathlib import Path

import numpy as np

from common.config import PaperClipConfig
from common.types import SymbolGrid
from serialization.encode.encoder import compute_total_pages, payload_to_symbol_grids, prepare_payload
from serialization.encode.frame_payload import PreparedPayload
from serialization.encode.pipeline import render_pages


def render_arrays(
    raw: bytes,
    config: PaperClipConfig,
    filename: str = "sample.bin",
    passphrase: str | None = None,
) -> list[np.ndarray]:
    images, _prepared, _grids = render_document(raw, config, filename, passphrase)
    return images


def render_document(
    raw: bytes,
    config: PaperClipConfig,
    filename: str = "sample.bin",
    passphrase: str | None = None,
) -> tuple[list[np.ndarray], PreparedPayload, list[SymbolGrid]]:
    prepared = prepare_payload(raw, config, filename, passphrase)
    data_pages = compute_total_pages(len(prepared.payload), config)
    images = render_pages(Path(filename), config, prepared=prepared, passphrase=passphrase)
    grids = payload_to_symbol_grids(prepared.payload, config, data_pages)
    return [np.asarray(image) for image in images], prepared, grids
