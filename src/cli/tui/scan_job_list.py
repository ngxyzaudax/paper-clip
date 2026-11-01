import json
from pathlib import Path
from typing import NamedTuple

from common.data_store import SCAN_JOBS_DIR


class ScanJob(NamedTuple):
    job_id: str
    folder: Path
    pages: int
    dpi: int
    created: str


def discover_scan_jobs(root: Path = SCAN_JOBS_DIR) -> list[ScanJob]:
    """Scan jobs with at least one page, newest first."""
    if not root.exists():
        return []
    jobs = [_scan_job(folder) for folder in sorted(root.iterdir(), reverse=True) if folder.is_dir()]
    return [job for job in jobs if job.pages]


def scan_job_option(job: ScanJob) -> tuple[str, str]:
    return f"{job.job_id} · {job.pages} page(s) · {job.dpi} DPI", job.job_id


def scan_job_details(job: ScanJob) -> str:
    return (
        f"[bold]Job[/bold]: {job.job_id}\n"
        f"[bold]Created[/bold]: {job.created.replace('T', ' ')[:19] or '(unknown)'}\n"
        f"[bold]Pages[/bold]: {job.pages}\n"
        f"[bold]Scan DPI[/bold]: {job.dpi or 'unknown'}\n"
        f"[bold]Folder[/bold]: {job.folder}"
    )


def _scan_job(folder: Path) -> ScanJob:
    meta = _metadata(folder / "job.json")
    pages = len(list((folder / "scans").glob("*.png"))) if (folder / "scans").exists() else 0
    return ScanJob(folder.name, folder, pages, int(meta.get("dpi", 0) or 0), str(meta.get("created", "")))


def _metadata(path: Path) -> dict[str, object]:
    try:
        raw = json.loads(path.read_text())
    except (OSError, ValueError):
        return {}
    return raw if isinstance(raw, dict) else {}
