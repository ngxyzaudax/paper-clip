from collections.abc import Callable
from pathlib import Path

import numpy as np
from fastapi import HTTPException
from PIL import Image

from serialization.decode.identify import identify_scan
from web.page_quality import page_quality
from web.wizard_present import present
from web.wizard_record import commit_scan
from workflows.print_jobs import PrintJob, job_by_id
from workflows.scan_jobs import start_scan_job
from workflows.wizard_state import revise_wizard, save_wizard, session_dir


def open_session(duplex: bool | None, print_job_id: str, scanner: str = "upload", dpi: int = 300) -> dict[str, object]:
    job = required_print_job(print_job_id)
    context = start_scan_job(scanner or "upload", dpi or 300)
    save_wizard(context.job_id, seed_wizard(duplex, print_job_id, job))
    return present(context.job_id)


def note_file(job_id: str, path: Path, dpi: int | None = None, mode: str = "") -> None:
    image = rgb_array(path)
    commit_scan(job_id, path.name, identify_scan(image), page_quality(image), dpi, mode)


def session_path(job_id: str) -> Path:
    return session_dir(job_id)


def apply_setup(job_id: str, duplex: bool | None, print_job_id: str | None) -> dict[str, object]:
    revise_wizard(job_id, _setup(duplex, print_job_id))
    return present(job_id)


def required_print_job(print_job_id: str) -> PrintJob | None:
    if not print_job_id:
        return None
    job = job_by_id(print_job_id)
    if job is None:
        raise HTTPException(404, "Print job not found")
    return job


def seed_wizard(duplex: bool | None, print_job_id: str, job: PrintJob | None) -> dict[str, object]:
    return {
        "duplex": chosen_duplex(duplex, job),
        "print_job_id": print_job_id,
        "sha256": job.original_sha256 if job else "",
        "total_pages": job.total_pages if job else 0,
        "data_pages": job.data_pages if job else 0,
        "passphrase_required": False,
        "scans": [],
    }


def chosen_duplex(requested: bool | None, job: PrintJob | None) -> bool:
    if requested is not None:
        return requested
    return bool(job and job.sides == 2)


def rgb_array(path: Path) -> np.ndarray:
    with Image.open(path) as img:
        return np.array(img.convert("RGB"))


def _setup(
    duplex: bool | None,
    print_job_id: str | None,
) -> Callable[[dict[str, object]], dict[str, object]]:
    def revise(wizard: dict[str, object]) -> dict[str, object]:
        return assigned_setup(wizard, duplex, print_job_id)
    return revise


def assigned_setup(wizard: dict[str, object], duplex: bool | None, print_job_id: str | None) -> dict[str, object]:
    updated = wizard if duplex is None else {**wizard, "duplex": duplex}
    if print_job_id is None:
        return updated
    return {**updated, "print_job_id": print_job_id}
