import logging
from pathlib import Path
from typing import NamedTuple

import numpy as np

from health.report import HealthReport, measure_health
from health.wrong_cells import observed_wrong
from serialization.decode.assemble import assemble_pages, best_pages, compatible_header
from serialization.decode.assemble_slots import Assembly
from serialization.decode.decode_passes import OnDecodeProgress, first_pass, report_progress, retry_pass
from serialization.decode.errors import DecodeError, LostDocument, PassphraseError
from serialization.decode.load_scan import load_scans
from serialization.decode.observation import PageObservation
from serialization.encode.qr_header import DecodedQrHeader

logger = logging.getLogger(__name__)

MODEL_READER = "cell model"
COLOUR_READER = "nearest colour"


class Decoded(NamedTuple):
    raw: bytes
    filename: str
    header: DecodedQrHeader
    health: HealthReport
    reader: str
    observed: tuple[PageObservation, ...]
    wrong_cells: tuple[np.ndarray, ...]


def decode(
    source: Path | list[np.ndarray] | np.ndarray,
    output_path: Path | None = None,
    passphrase: str | None = None,
    model_path: Path | None = None,
    use_model: bool | None = None,
) -> tuple[bytes, str]:
    decoded = decode_document(source, passphrase, model_path, use_model)
    if output_path is not None:
        _write_output(decoded, output_path)
    return decoded.raw, decoded.filename


def decode_document(
    source: Path | list[np.ndarray] | np.ndarray,
    passphrase: str | None = None,
    model_path: Path | None = None,
    use_model: bool | None = None,
    on_page: OnDecodeProgress | None = None,
) -> Decoded:
    """Recover the file and measure how much repair margin the printed pages have left."""
    images = list(load_scans(source))
    model = _load_model(model_path, use_model)
    assembly, reader = _recover(images, model, passphrase, on_page)
    wrong = observed_wrong(assembly)
    health = measure_health(assembly, wrong)
    report_progress(on_page, len(images), len(images), "verify")
    return Decoded(assembly.raw, assembly.filename, assembly.header, health, reader, assembly.observed, wrong)


def _write_output(decoded: Decoded, output_path: Path) -> Path:
    destination = output_path / decoded.filename if output_path.is_dir() else output_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(decoded.raw)
    logger.info("Wrote %s (%d bytes)", destination, len(decoded.raw))
    return destination


def _recover(
    images: list[np.ndarray],
    model: object | None,
    passphrase: str | None,
    on_page: OnDecodeProgress | None,
) -> tuple[Assembly, str]:
    if model is None:
        return _assemble(images, None, passphrase, on_page), COLOUR_READER
    try:
        return _assemble(images, model, passphrase, on_page), MODEL_READER
    except PassphraseError:
        raise
    except DecodeError:
        logger.info("Cell model left the payload unreadable; retrying with nearest colour")
        return _assemble(images, None, passphrase, on_page), COLOUR_READER


def _assemble(
    images: list[np.ndarray],
    model: object | None,
    passphrase: str | None,
    on_page: OnDecodeProgress | None,
) -> Assembly:
    pages, pending = first_pass(images, model, on_page)
    if pending:
        hints = tuple(page.header for page in pages if page.header.page_index >= 0)
        pages.extend(retry_pass(pending, model, hints, len(images), on_page))
    if not pages:
        raise DecodeError("page header not found")
    logger.info("Read headers from %d scan(s)", len(pages))
    report_progress(on_page, len(pages), len(images), "repair")
    try:
        return assemble_pages(pages, passphrase)
    except (PassphraseError, LostDocument):
        raise
    except DecodeError as exc:
        raise _lost(exc, pages) from exc


def _lost(exc: DecodeError, pages: list[PageObservation]) -> LostDocument:
    header = compatible_header(pages)
    scanned = tuple(sorted({page.header.page_index for page in pages if page.header.page_index >= 0}))
    return LostDocument(f"data is no longer recoverable: {exc}", header, scanned, best_pages(pages))


def _load_model(model_path: Path | None, use_model: bool | None) -> object | None:
    if use_model is False:
        return None
    from ml.store import load_cell_model

    return load_cell_model(model_path, required=use_model is True)
