from collections.abc import Callable
from pathlib import Path
from typing import NamedTuple

import numpy as np

from health.damage_render import DamageImages, save_damage_image
from health.header_note import header_summary
from health.reading import Reading, Tracked
from health.report import lost_health
from serialization.decode.observation import PageObservation
from health.store import load_tracked, record_reading
from health.trend import now_stamp
from serialization.decode.errors import LostDocument
from serialization.decode.pipeline import Decoded, decode_document

LOST_READER = "every reader"
IN_MEMORY_SOURCE = "images in memory"


class HealthCheck(NamedTuple):
    sha256: str
    filename: str
    reading: Reading
    history: Tracked
    saved: bool
    decoded: Decoded | None


def run_check(
    source: Path | list[np.ndarray],
    passphrase: str | None = None,
    model_path: Path | None = None,
    use_model: bool | None = None,
    track: bool = True,
    on_page: Callable[[int, int, str], None] | None = None,
) -> HealthCheck:
    """Decode the scans, rate the paper, draw where it is damaged, and record the reading unless told not to."""
    try:
        decoded = decode_document(source, passphrase, model_path, use_model, on_page=on_page)
    except LostDocument as lost:
        return _lost_check(lost, source, track)
    header = decoded.header
    sha256 = header.original_sha256.hex()
    stamp = now_stamp()
    saved = save_damage_image(
        sha256, decoded.filename, stamp, decoded.health, decoded.observed, decoded.wrong_cells,
    )
    reading = Reading(stamp, source_label(source), decoded.reader, decoded.health, *_damage_fields(saved))
    return _checked(sha256, decoded.filename, header.original_length, reading, track, decoded)


def _lost_check(lost: LostDocument, source: Path | list[np.ndarray], track: bool) -> HealthCheck:
    header = lost.header
    sha256 = header.original_sha256.hex()
    previous = load_tracked(sha256)
    filename = previous.filename if previous else ""
    stamp = now_stamp()
    observed = tuple(page for page in lost.observed if isinstance(page, PageObservation))
    report = lost_health(header, lost.scanned, header_summary(observed))
    saved = save_damage_image(sha256, filename, stamp, report, lost.observed, ())
    reading = Reading(stamp, source_label(source), LOST_READER, report, *_damage_fields(saved))
    return _checked(sha256, filename, header.original_length, reading, track, None)


def _damage_fields(saved: DamageImages | None) -> tuple[str, tuple[str, ...]]:
    if saved is None:
        return "", ()
    return str(saved.sheet), tuple(str(path) for path in saved.pages)


def source_label(source: Path | list[np.ndarray]) -> str:
    return str(source) if isinstance(source, (str, Path)) else IN_MEMORY_SOURCE


def _checked(
    sha256: str, filename: str, size: int, reading: Reading, track: bool, decoded: Decoded | None,
) -> HealthCheck:
    if track:
        history = record_reading(sha256, filename, size, reading)
        return HealthCheck(sha256, history.filename, reading, history, True, decoded)
    previous = load_tracked(sha256)
    name = filename or (previous.filename if previous else "")
    readings = (previous.readings if previous else ()) + (reading,)
    return HealthCheck(sha256, name, reading, Tracked(sha256, name, size, readings), False, decoded)
