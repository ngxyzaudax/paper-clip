from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from common.data_store import create_scan_job, scans_dir

SCAN_PAGE_PREFIX = "scan_"
SCAN_PAGE_SUFFIX = ".png"
SCAN_PAGE_PADDING = 3


@dataclass(frozen=True)
class ScanJobContext:
    job_dir: Path
    job_id: str
    scanner_name: str
    dpi: int


def start_scan_job(scanner_name: str, dpi: int, mode: str = "") -> ScanJobContext:
    if not scanner_name:
        raise ValueError("scanner_name is required")
    if dpi <= 0:
        raise ValueError("dpi must be a positive integer")
    job_dir = create_scan_job(scanner_name, dpi, mode=mode)
    return ScanJobContext(
        job_dir=job_dir,
        job_id=job_dir.name,
        scanner_name=scanner_name,
        dpi=dpi,
    )


def _scan_index_from_filename(name: str) -> int:
    if not name.startswith(SCAN_PAGE_PREFIX) or not name.endswith(SCAN_PAGE_SUFFIX):
        return 0
    raw = name[len(SCAN_PAGE_PREFIX): -len(SCAN_PAGE_SUFFIX)]
    return int(raw) if raw.isdigit() else 0


def _existing_scan_indices(target_dir: Path) -> list[int]:
    if not target_dir.exists():
        return []
    return sorted(
        _scan_index_from_filename(p.name)
        for p in target_dir.iterdir()
        if p.is_file()
    )


def next_scan_path(job_dir: Path) -> Path:
    target_dir = scans_dir(job_dir)
    indices = _existing_scan_indices(target_dir)
    next_idx = (indices[-1] if indices else 0) + 1
    filename = f"{SCAN_PAGE_PREFIX}{next_idx:0{SCAN_PAGE_PADDING}d}{SCAN_PAGE_SUFFIX}"
    return target_dir / filename


def count_scans(job_dir: Path) -> int:
    target_dir = job_dir / "scans"
    if not target_dir.exists():
        return 0
    return sum(1 for p in target_dir.iterdir() if p.is_file())


def update_scan_job_metadata(job_dir: Path, last_capture_dpi: int, last_mode: str) -> None:
    meta_path = job_dir / "job.json"
    if not meta_path.exists():
        return
    try:
        raw = json.loads(meta_path.read_text())
    except Exception:
        return
    if not isinstance(raw, dict):
        return
    raw["dpi"] = last_capture_dpi
    if last_mode:
        raw["mode"] = last_mode
    raw["pages"] = count_scans(job_dir)
    meta_path.write_text(json.dumps(raw, indent=2))
