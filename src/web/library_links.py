from pathlib import Path

from health.reading import Tracked
from health.store import all_tracked
from workflows.print_jobs import PrintJob


def names_by_file(documents: dict[str, dict[str, object]]) -> dict[str, str]:
    return {str(doc["filename"]): sha for sha, doc in documents.items() if doc.get("filename")}


def scan_owners() -> dict[str, str]:
    owners: dict[str, str] = {}
    for item in all_tracked():
        owners.update(_owners(item))
    return owners


def linked_print_sha(job: PrintJob, names: dict[str, str]) -> str:
    return job.original_sha256 or names.get(job.source_file, "")


def linked_scan_sha(job_id: str, wizard_sha: str, owners: dict[str, str]) -> str:
    return wizard_sha or owners.get(job_id, "")


def _owners(item: Tracked) -> dict[str, str]:
    return {Path(reading.source).name: item.sha256 for reading in item.readings if reading.source}
