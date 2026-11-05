from workflows.scan_list import ScanJob, discover_scan_jobs
from workflows.wizard_state import load_wizard


def session_rows() -> list[dict[str, object]]:
    return [session_row(job) for job in discover_scan_jobs(include_empty=True)]


def session_row(job: ScanJob) -> dict[str, object]:
    return {"job_id": job.job_id, "pages": job.pages, "created": job.created, "sha256": session_sha(job.job_id)}


def session_sha(job_id: str) -> str:
    try:
        return str(load_wizard(job_id).get("sha256") or "")
    except (OSError, ValueError):
        return ""
