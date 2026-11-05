from pathlib import Path

from common.data_store import DATA_ROOT
from health.reading import latest
from health.status import status_of
from health.store import all_tracked, load_tracked
from web.library_links import linked_print_sha, linked_scan_sha, names_by_file, scan_owners
from web.present import print_summary
from web.sniff import file_sha256
from workflows.print_jobs import discover_print_jobs
from workflows.scan_list import ScanJob, discover_scan_jobs, scan_paths
from workflows.wizard_state import load_wizard

PRINT_FIELDS = ("job_id", "created", "pages", "data_pages", "sides", "paper_size", "page_names")


def library_index() -> dict[str, object]:
    documents: dict[str, dict[str, object]] = {}
    unlinked: list[dict[str, str]] = []
    _health(documents)
    _prints(documents, unlinked, names_by_file(documents))
    _scans(documents, unlinked, scan_owners())
    return {"documents": list(documents.values()), "unlinked": unlinked}


def library_detail(sha: str) -> dict[str, object]:
    tracked = load_tracked(sha)
    name = tracked.filename if tracked else ""
    names = {name: sha} if name else {}
    owners = scan_owners()
    prints = [print_summary(job) for job in discover_print_jobs() if linked_print_sha(job, names) == sha]
    scans = [_scan(job) for job in discover_scan_jobs() if linked_scan_sha(job.job_id, _scan_sha(job.job_id), owners) == sha]
    return {
        "sha256": sha,
        "filename": tracked.filename if tracked else _filename(prints),
        "prints": [{key: item[key] for key in PRINT_FIELDS} for item in prints],
        "scans": scans,
        "recovered": _recovered(sha),
        "readings": _readings(tracked),
    }


def _prints(documents: dict[str, dict[str, object]], unlinked: list[dict[str, str]], names: dict[str, str]) -> None:
    for job in discover_print_jobs():
        sha = linked_print_sha(job, names)
        if not sha:
            unlinked.append({"kind": "print", "id": job.job_id, "label": job.source_file or job.job_id})
            continue
        doc = documents.setdefault(sha, _blank(sha, job.source_file))
        doc["pages"] = max(int(doc["pages"]), len(job.page_paths))
        doc["job_id"] = doc["job_id"] or job.job_id
        doc["filename"] = doc["filename"] or job.source_file


def _health(documents: dict[str, dict[str, object]]) -> None:
    for item in all_tracked():
        doc = documents.setdefault(item.sha256, _blank(item.sha256, item.filename))
        reading = latest(item)
        doc["filename"] = item.filename or doc["filename"]
        doc["health"] = reading.report.health
        doc["status"] = status_of(reading.report).label


def _scans(documents: dict[str, dict[str, object]], unlinked: list[dict[str, str]], owners: dict[str, str]) -> None:
    for job in discover_scan_jobs():
        sha = linked_scan_sha(job.job_id, _scan_sha(job.job_id), owners)
        if not sha:
            unlinked.append({"kind": "scan", "id": job.job_id, "label": f"Scan · {job.created[:10]}"})
            continue
        doc = documents.setdefault(sha, _blank(sha, ""))
        doc["job_id"] = doc["job_id"] or job.job_id


def _blank(sha: str, filename: str) -> dict[str, object]:
    return {"sha256": sha, "filename": filename, "pages": 0, "health": None, "status": None, "job_id": ""}


def _scan_sha(job_id: str) -> str:
    try:
        return str(load_wizard(job_id).get("sha256") or "")
    except OSError:
        return ""


def _scan(job: ScanJob) -> dict[str, object]:
    return {"job_id": job.job_id, "pages": job.pages, "created": job.created, "names": [path.name for path in scan_paths(job.folder)]}


def _filename(prints: list[dict[str, object]]) -> str:
    if not prints:
        return ""
    return str(prints[0].get("source_file", ""))


def _readings(tracked: object) -> list[dict[str, object]]:
    if tracked is None:
        return []
    return [
        {"time": reading.time, "health": reading.report.health, "status": status_of(reading.report).label}
        for reading in tracked.readings
    ]


def _recovered(sha: str) -> list[dict[str, str]]:
    root = DATA_ROOT / "decoded"
    if not root.is_dir():
        return []
    found = []
    for path in root.glob("*/*"):
        if path.is_file() and file_sha256(path) == sha:
            found.append({"job_id": path.parent.name, "name": path.name})
    return found
