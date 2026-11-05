import logging
from datetime import datetime
from pathlib import Path
from typing import NamedTuple

from common.data_store import SCAN_JOBS_DIR
from common.json_file import JsonFileError, read_json_object

logger = logging.getLogger(__name__)

SCAN_SUFFIXES = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}


class ScanJob(NamedTuple):
    job_id: str
    folder: Path
    pages: int
    dpi: int
    created: str


def discover_scan_jobs(root: Path = SCAN_JOBS_DIR, include_empty: bool = False) -> list[ScanJob]:
    if not root.is_dir():
        return []
    jobs = [job for job in (_scan_job(folder) for folder in root.iterdir() if folder.is_dir()) if job is not None]
    return sorted(_visible(jobs, include_empty), key=_by_created, reverse=True)


def scan_paths(folder: Path) -> list[Path]:
    return sorted(_images(_page_dir(folder)), key=_path_name)


def _visible(jobs: list[ScanJob], include_empty: bool) -> list[ScanJob]:
    if include_empty:
        return jobs
    return [job for job in jobs if job.pages]


def _by_created(job: ScanJob) -> str:
    return job.created


def _scan_job(folder: Path) -> ScanJob | None:
    try:
        return _loaded(folder, read_json_object(folder / "job.json"))
    except (JsonFileError, OSError, ValueError) as exc:
        logger.warning("Skipping scan job with unreadable metadata: %s (%s)", folder.name, exc)
        return None


def _loaded(folder: Path, meta: dict[str, object]) -> ScanJob:
    return ScanJob(folder.name, folder, len(scan_paths(folder)), int(meta.get("dpi", 0) or 0), _created(folder, meta))


def _created(folder: Path, meta: dict[str, object]) -> str:
    stored = str(meta.get("created", ""))
    if stored:
        return stored
    return datetime.fromtimestamp(folder.stat().st_mtime).isoformat()


def _page_dir(folder: Path) -> Path:
    pages = folder / "scans"
    if pages.is_dir():
        return pages
    return folder


def _images(folder: Path) -> list[Path]:
    return [item for item in folder.iterdir() if item.is_file() and item.suffix.lower() in SCAN_SUFFIXES]


def _path_name(path: Path) -> str:
    return path.name
