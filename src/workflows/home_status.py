from calibration.profile import load_density_profile
from common.device_config import get_printer_settings, get_scanner_settings
from health.reading import Tracked, latest
from health.status import status_of
from health.store import all_tracked
from workflows.print_jobs import PrintJob, discover_print_jobs
from workflows.scan_list import ScanJob, discover_scan_jobs


def home_snapshot() -> dict[str, object]:
    prints = discover_print_jobs()
    scans = discover_scan_jobs()
    tracked = all_tracked()
    return {
        "printer": _printer(),
        "scanner": _scanner(),
        "profile": _profile(),
        "health": _health(tracked),
        "newest_print": _print(prints[0]) if prints else None,
        "newest_scan": _scan(scans[0]) if scans else None,
        "latest_check": _check(tracked),
        "attention": _attention(tracked),
    }


def _printer() -> dict[str, str]:
    settings = get_printer_settings()
    return {"name": str(settings.get("name", "")), "uri": str(settings.get("uri", ""))}


def _scanner() -> dict[str, str]:
    settings = get_scanner_settings()
    return {"device": str(settings.get("device", "")), "uri": str(settings.get("uri", ""))}


def _profile() -> dict[str, object] | None:
    saved = load_density_profile()
    if saved is None:
        return None
    return {"cell_size_px": saved.cell_size_px, "num_symbols": saved.num_symbols, "print_dpi": saved.print_dpi}


def _health(tracked: list[Tracked]) -> dict[str, int]:
    flagged = sum(status_of(latest(item).report).label not in ("Healthy", "Worn") for item in tracked)
    return {"tracked": len(tracked), "flagged": flagged}


def _print(job: PrintJob) -> dict[str, object]:
    return {"job_id": job.job_id, "source_file": job.source_file, "pages": len(job.page_paths)}


def _scan(job: ScanJob) -> dict[str, object]:
    return {"job_id": job.job_id, "pages": job.pages, "created": job.created}


def _check(tracked: list[Tracked]) -> dict[str, object] | None:
    if not tracked:
        return None
    item = tracked[0]
    reading = latest(item)
    return {
        "sha256": item.sha256,
        "filename": item.filename,
        "health": reading.report.health,
        "status": status_of(reading.report).label,
        "time": reading.time,
    }


def _attention(tracked: list[Tracked]) -> list[dict[str, object]]:
    return [row for row in (_attention_row(item) for item in tracked) if row is not None]


def _attention_row(item: Tracked) -> dict[str, object] | None:
    reading = latest(item)
    status = status_of(reading.report)
    if status.label in ("Healthy", "Worn"):
        return None
    return {"sha256": item.sha256, "filename": item.filename, "health": reading.report.health, "status": status.label}
