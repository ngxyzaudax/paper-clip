from datetime import datetime
from pathlib import Path

from calibration.sheet_io import calibration_dir
from workflows.print_jobs import PrintJob, discover_print_jobs
from workflows.scan_list import ScanJob, discover_scan_jobs, scan_paths

CALIBRATION_SHEETS = ("front.png", "back.png")
ARCHIVED_SESSION_PREFIX = "session-"


def archive_index() -> dict[str, list[dict[str, object]]]:
    return {
        "print": [_print_group(job) for job in discover_print_jobs()],
        "scan": [_scan_group(job) for job in discover_scan_jobs()],
        "calibration": _calibration_groups(calibration_dir()),
    }


def calibration_path(root: Path, ident: str, name: str) -> Path:
    if ident == "sheet":
        return root / name
    if ident.startswith(ARCHIVED_SESSION_PREFIX):
        return root / "archive" / ident / name
    return root / ident / name


def _group(kind: str, ident: str, label: str, detail: str, created: str, names: list[str]) -> dict[str, object]:
    return {"kind": kind, "ident": ident, "label": label, "detail": detail, "created": created, "names": names}


def counted(amount: int, noun: str) -> str:
    return f"{amount} {noun}" if amount == 1 else f"{amount} {noun}s"


def _print_group(job: PrintJob) -> dict[str, object]:
    sides = "both sides" if job.sides == 2 else "one side"
    detail = f"{counted(len(job.page_paths), 'page')} · {job.paper_size or 'paper'} · {sides}"
    return _group("print", job.job_id, job.source_file or job.job_id, detail, job.created, [path.name for path in job.page_paths])


def _scan_group(job: ScanJob) -> dict[str, object]:
    return _group("scan", job.job_id, f"Scan · {_day(job.created)}", counted(job.pages, "scan"), job.created, [path.name for path in scan_paths(job.folder)])


def _calibration_groups(root: Path) -> list[dict[str, object]]:
    sheets = [name for name in CALIBRATION_SHEETS if (root / name).is_file()]
    current = _images(root / "session")
    archived = sorted((root / "archive").glob(f"{ARCHIVED_SESSION_PREFIX}*"), reverse=True) if (root / "archive").is_dir() else []
    groups = [
        _group("calibration", "sheet", "Calibration sheet", "Front and back", _stamp(root / "front.png"), sheets),
        _group("calibration", "session", "Current session", counted(len(current), "scan"), _stamp(root / "session"), current),
        *(_archived(folder) for folder in archived),
    ]
    return [group for group in groups if group["names"]]


def _archived(folder: Path) -> dict[str, object]:
    names = _images(folder)
    return _group("calibration", folder.name, f"Archived {folder.name}", counted(len(names), "scan"), _stamp(folder), names)


def _images(folder: Path) -> list[str]:
    return sorted(path.name for path in folder.glob("*.png")) if folder.is_dir() else []


def _day(stamp: str) -> str:
    try:
        when = datetime.fromisoformat(stamp)
    except ValueError:
        return stamp
    return f"{when.day} {when.strftime('%b %Y')}"


def _stamp(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds") if path.exists() else ""
