from pathlib import Path

import numpy as np

from common.config import PaperClipConfig
from serialization.encode.encoder import prepare_payload
from serialization.encode.pipeline import render_pages


def render_arrays(
    raw: bytes,
    config: PaperClipConfig,
    filename: str = "sample.bin",
    passphrase: str | None = None,
) -> list[np.ndarray]:
    prepared = prepare_payload(raw, config, filename, passphrase)
    images = render_pages(Path(filename), config, prepared=prepared, passphrase=passphrase)
    return [np.asarray(image) for image in images]
