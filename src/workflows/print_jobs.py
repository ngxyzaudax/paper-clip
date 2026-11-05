from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from common.data_store import PRINT_JOBS_DIR
from common.json_file import read_json_object

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PrintJob:
    job_id: str
    source_file: str
    created: str
    paper_size: str
    page_paths: tuple[Path, ...]
    data_pages: int = 0
    total_pages: int = 0
    original_sha256: str = ""
    payload_bytes: int = 0
    prints: tuple[dict[str, object], ...] = ()
    job_dir: Path | None = None
    sides: int = 1


def discover_print_jobs() -> list[PrintJob]:
    return _newest([job for job in _jobs() if job.page_paths])


def job_by_id(job_id: str) -> PrintJob | None:
    folder = _folder(job_id)
    if folder is None:
        return None
    job = _loaded(folder)
    if job is None or not job.page_paths:
        return None
    return job


def _jobs() -> list[PrintJob]:
    if not PRINT_JOBS_DIR.is_dir():
        return []
    loaded = [_loaded(folder) for folder in PRINT_JOBS_DIR.iterdir() if folder.is_dir()]
    return [job for job in loaded if job is not None]


def _newest(jobs: list[PrintJob]) -> list[PrintJob]:
    return sorted(jobs, key=_created, reverse=True)


def _created(job: PrintJob) -> str:
    return job.created


def _folder(job_id: str) -> Path | None:
    if not _safe_job_id(job_id):
        return None
    root = PRINT_JOBS_DIR.resolve()
    folder = (PRINT_JOBS_DIR / job_id).resolve()
    if folder.parent != root or not folder.is_dir():
        return None
    return folder


def _safe_job_id(job_id: str) -> bool:
    if not job_id or job_id in {".", ".."} or "/" in job_id or "\\" in job_id:
        return False
    return Path(job_id).name == job_id


def _loaded(folder: Path) -> PrintJob | None:
    try:
        return _job(folder)
    except (OSError, ValueError) as exc:
        logger.warning("Skipping print job %s: %s", folder.name, exc)
        return None


def _job(job_dir: Path) -> PrintJob:
    meta = read_json_object(job_dir / "job.json")
    return PrintJob(
        job_id=job_dir.name,
        source_file=str(meta.get("source_file", "")),
        created=str(meta.get("created", "")),
        paper_size=str(meta.get("paper_size", "")),
        page_paths=_pages(job_dir),
        data_pages=_count(meta, "data_pages"),
        total_pages=_count(meta, "total_pages"),
        original_sha256=str(meta.get("original_sha256", "")),
        payload_bytes=_count(meta, "payload_bytes"),
        prints=_prints(meta),
        job_dir=job_dir,
        sides=_sides(meta),
    )


def _pages(job_dir: Path) -> tuple[Path, ...]:
    digital = job_dir / "digital"
    if not digital.is_dir():
        return ()
    numbered = sorted(digital.glob("page_*.png"))
    if numbered:
        return tuple(numbered)
    single = digital / "page.png"
    return (single,) if single.is_file() else ()


def _count(meta: dict[str, object], key: str) -> int:
    raw = meta.get(key, 0) or 0
    if isinstance(raw, bool):
        raise ValueError(f"Invalid {key} in job metadata")
    try:
        return int(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid {key} in job metadata") from exc


def _prints(meta: dict[str, object]) -> tuple[dict[str, object], ...]:
    found = meta.get("prints", [])
    if not isinstance(found, list):
        return ()
    return tuple(item for item in found if isinstance(item, dict))


def _sides(meta: dict[str, object]) -> int:
    return 2 if meta.get("sides") == 2 else 1
