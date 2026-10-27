import logging
from pathlib import Path

import numpy as np

from serialization.decode.assemble import assemble_pages
from serialization.decode.load_scan import load_scans
from serialization.decode.observe import observe_page

logger = logging.getLogger(__name__)


def decode(
    source: Path | list[np.ndarray] | np.ndarray,
    output_path: Path | None = None,
    passphrase: str | None = None,
    model_path: Path | None = None,
    use_model: bool | None = None,
) -> tuple[bytes, str]:
    model = _load_model(model_path, use_model)
    pages = [observe_page(image, model) for image in load_scans(source)]
    logger.info("Decoded QR headers from %d scan(s)", len(pages))
    raw, filename = assemble_pages(pages, passphrase)
    if output_path is not None:
        destination = output_path / filename if output_path.is_dir() else output_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(raw)
        logger.info("Wrote %s (%d bytes)", destination, len(raw))
    return raw, filename


def _load_model(model_path: Path | None, use_model: bool | None):
    if use_model is False:
        return None
    from ml.store import load_cell_model

    return load_cell_model(model_path, required=use_model is True)
