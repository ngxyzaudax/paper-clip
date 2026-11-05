from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from common.data_store import create_scan_job, scans_dir
from common.json_file import JsonObject, read_json_object, update_json_object
from workflows.scan_list import SCAN_SUFFIXES, scan_paths

SCAN_PAGE_PREFIX = "scan_"
SCAN_PAGE_SUFFIX = ".png"


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
    return ScanJobContext(job_dir, job_dir.name, scanner_name, dpi)


def next_scan_path(job_dir: Path, suffix: str = SCAN_PAGE_SUFFIX) -> Path:
    target = scans_dir(job_dir)
    return _claim(target, _highest_index(target) + 1, _suffix(suffix))


def count_scans(job_dir: Path) -> int:
    if not job_dir.is_dir():
        return 0
    return len(scan_paths(job_dir))


def update_scan_job_metadata(job_dir: Path, last_capture_dpi: int, last_mode: str) -> None:
    path = job_dir / "job.json"
    if not path.is_file():
        return
    update_json_object(path, _capture_change(job_dir, last_capture_dpi, last_mode))


def read_job(job_dir: Path) -> dict[str, object]:
    return read_json_object(job_dir / "job.json")


def write_job(job_dir: Path, meta: dict[str, object]) -> None:
    update_json_object(job_dir / "job.json", _replace(meta))


def _claim(folder: Path, index: int, suffix: str) -> Path:
    path = _page_path(folder, index, suffix)
    try:
        _create_exclusive(path)
    except FileExistsError:
        return _claim(folder, index + 1, suffix)
    return path


def _create_exclusive(path: Path) -> None:
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    os.close(fd)


def _page_path(folder: Path, index: int, suffix: str) -> Path:
    return folder / f"{SCAN_PAGE_PREFIX}{index:03d}{suffix}"


def _highest_index(folder: Path) -> int:
    found = [_page_index(path.name) for path in folder.iterdir() if path.is_file()]
    if not found:
        return 0
    return max(found)


def _page_index(name: str) -> int:
    suffix = Path(name).suffix.lower()
    if suffix not in SCAN_SUFFIXES or not name.startswith(SCAN_PAGE_PREFIX):
        return 0
    raw = name[len(SCAN_PAGE_PREFIX):-len(suffix)]
    if not raw.isdigit():
        return 0
    return int(raw)


def _suffix(suffix: str) -> str:
    if suffix in SCAN_SUFFIXES:
        return suffix
    return SCAN_PAGE_SUFFIX


def _capture_change(job_dir: Path, dpi: int, mode: str) -> Callable[[JsonObject], JsonObject]:
    def change(raw: JsonObject) -> JsonObject:
        return _with_capture(raw, dpi, mode, count_scans(job_dir))
    return change


def _with_capture(raw: JsonObject, dpi: int, mode: str, pages: int) -> JsonObject:
    updated: JsonObject = {**raw, "dpi": dpi, "pages": pages}
    if not mode:
        return updated
    return {**updated, "mode": mode}


def _replace(meta: dict[str, object]) -> Callable[[JsonObject], JsonObject]:
    def change(_current: JsonObject) -> JsonObject:
        return {**meta}
    return change
