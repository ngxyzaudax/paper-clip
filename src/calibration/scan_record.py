import json
from pathlib import Path
from typing import NamedTuple

import numpy as np
from PIL import Image

from calibration.sheet_io import layout_fingerprint
from calibration.sheet_score import PatchRead, read_scan


_READER = 3


class ScanRecord(NamedTuple):
    name: str
    side: str
    rotation: int
    reads: tuple[PatchRead, ...]


def scan_record(scan: Path) -> ScanRecord:
    """Score one scan, reusing the cached result when it was made for the current sheet layout."""
    fingerprint = layout_fingerprint()
    cached = _load(scan, fingerprint)
    if cached is not None:
        return cached
    found = read_scan(_image(scan))
    record = ScanRecord(scan.name, found.side, found.rotation, found.reads)
    _save(scan, record, fingerprint)
    return record


def records_in(folder: Path) -> tuple[ScanRecord, ...]:
    if not folder.exists():
        return ()
    return tuple(scan_record(path) for path in sorted(folder.glob("*.png")))


def all_reads(records: tuple[ScanRecord, ...]) -> tuple[PatchRead, ...]:
    return tuple(read for record in records for read in record.reads)


def record_path(scan: Path) -> Path:
    return scan.with_suffix(".json")


def _load(scan: Path, fingerprint: str) -> ScanRecord | None:
    path = record_path(scan)
    if not path.exists() or path.stat().st_mtime < scan.stat().st_mtime:
        return None
    try:
        raw = json.loads(path.read_text())
        if raw.get("layout") != fingerprint or raw.get("reader") != _READER:
            return None
        reads = tuple(PatchRead(**item) for item in raw["reads"])
        return ScanRecord(scan.name, str(raw["side"]), int(raw["rotation"]), reads)
    except (OSError, ValueError, KeyError, TypeError):
        return None


def _save(scan: Path, record: ScanRecord, fingerprint: str) -> None:
    payload = {
        "layout": fingerprint,
        "reader": _READER,
        "side": record.side,
        "rotation": record.rotation,
        "reads": [read._asdict() for read in record.reads],
    }
    record_path(scan).write_text(json.dumps(payload, indent=1))


def _image(scan: Path) -> np.ndarray:
    Image.MAX_IMAGE_PIXELS = None
    return np.asarray(Image.open(scan).convert("RGB"))
