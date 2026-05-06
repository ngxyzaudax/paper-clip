from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from common.data_store import PRINT_JOBS_DIR


@dataclass(frozen=True)
class PrintJob:
    job_id: str
    source_file: str
    created: str
    paper_size: str
    page_paths: tuple[Path, ...]


def _read_job_metadata(job_dir: Path) -> dict[str, object]:
    meta_path = job_dir / "job.json"
    if not meta_path.exists():
        return {}
    try:
        raw = json.loads(meta_path.read_text())
    except Exception:
        return {}
    return raw if isinstance(raw, dict) else {}


def _list_digital_pages(job_dir: Path) -> tuple[Path, ...]:
    digital_dir = job_dir / "digital"
    if not digital_dir.exists():
        return ()
    single = digital_dir / "page.png"
    numbered = sorted(digital_dir.glob("page_*.png"))
    if numbered:
        return tuple(numbered)
    if single.exists():
        return (single,)
    return ()


def discover_print_jobs() -> list[PrintJob]:
    if not PRINT_JOBS_DIR.exists():
        return []
    jobs: list[PrintJob] = []
    for job_dir in sorted((p for p in PRINT_JOBS_DIR.iterdir() if p.is_dir()), reverse=True):
        pages = _list_digital_pages(job_dir)
        if not pages:
            continue
        meta = _read_job_metadata(job_dir)
        jobs.append(
            PrintJob(
                job_id=job_dir.name,
                source_file=str(meta.get("source_file", "")),
                created=str(meta.get("created", "")),
                paper_size=str(meta.get("paper_size", "")),
                page_paths=pages,
            ),
        )
    return jobs


def job_option_label(job: PrintJob) -> str:
    source = job.source_file if job.source_file else "(unknown source)"
    count = len(job.page_paths)
    paper = f" · {job.paper_size}" if job.paper_size else ""
    return f"{job.job_id} · {source} · {count} page(s){paper}"
