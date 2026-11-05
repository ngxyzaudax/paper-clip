from collections.abc import Callable
from pathlib import Path

from common.device_error import DeviceError
from common.sane_scan import ScanCaptureResult
from common.scan_capture import capture_page
from health.pages import PageHealth
from health.status import status_of
from serialization.decode.decode_passes import OnDecodeProgress
from web.decode_bodies import DecodeRequest
from web.present import media_urls
from web.tasks import TaskRecord, push
from web.wizard_logic import note_file, session_path
from workflows.decode_job import DecodeOutcome, decode_source
from workflows.scan_discovery import discover_scanners_for_scan, resolve_max_dpi
from workflows.scan_jobs import next_scan_path


def capture_task(job_id: str) -> Callable[[TaskRecord], dict[str, object]]:
    def run(record: TaskRecord) -> dict[str, object]:
        return run_capture(job_id, record)
    return run


def decode_task(job_id: str, body: DecodeRequest) -> Callable[[TaskRecord], dict[str, object]]:
    def run(record: TaskRecord) -> dict[str, object]:
        return run_decode(job_id, body, record)
    return run


def run_capture(job_id: str, record: TaskRecord) -> dict[str, object]:
    scanner = selected_scanner()
    dpi = resolve_max_dpi(scanner) or 1200
    path = next_scan_path(session_path(job_id))
    push(record, "progress", {"fraction": 0.2, "label": f"Scanning at {dpi} dpi"})
    captured = captured_page(scanner, path, dpi)
    note_file(job_id, path, captured.dpi, captured.mode)
    return {"message": f"Scanned {path.name}"}


def run_decode(job_id: str, body: DecodeRequest, record: TaskRecord) -> dict[str, object]:
    outcome = decode_source(
        session_path(job_id),
        job_id,
        secret_of(body.passphrase),
        flag_of(body.track, True),
        flag_of(body.save, True),
        on_page=progress_of(record),
    )
    return decode_result(outcome)


def selected_scanner() -> str:
    _found, selected = discover_scanners_for_scan()
    if not selected:
        raise ValueError("No scanner found")
    return selected


def captured_page(scanner: str, path: Path, dpi: int) -> ScanCaptureResult:
    try:
        return capture_page(scanner, path, dpi)
    except DeviceError as exc:
        raise ValueError(str(exc)) from exc


def secret_of(passphrase: str | None) -> str | None:
    if not passphrase:
        return None
    return passphrase


def flag_of(value: bool | None, default: bool) -> bool:
    if value is None:
        return default
    return value


def progress_of(record: TaskRecord) -> OnDecodeProgress:
    def report(index: int, total: int, stage: str) -> None:
        fraction = (index + 1) / max(total, 1)
        push(record, "progress", {"fraction": fraction, "label": f"{stage} {index + 1}/{total}"})
    return report


def decode_result(outcome: DecodeOutcome) -> dict[str, object]:
    reading = outcome.check.reading
    status = status_of(reading.report)
    return {
        "filename": result_filename(outcome),
        "saved_path": str(outcome.path or ""),
        "sha256": outcome.check.sha256,
        "health": reading.report.health,
        "status": status.label,
        "advice": status.advice,
        "lost": result_lost(outcome),
        "damage_pages": media_urls(reading.damage_pages),
        "pages": [result_page(page) for page in reading.report.pages],
    }


def result_filename(outcome: DecodeOutcome) -> str:
    decoded = outcome.check.decoded
    if decoded is None:
        return outcome.check.filename
    return decoded.filename


def result_lost(outcome: DecodeOutcome) -> bool:
    return bool(outcome.check.reading.report.lost or outcome.check.decoded is None)


def result_page(page: PageHealth) -> dict[str, object]:
    return {
        "index": page.index,
        "damaged": page.damaged,
        "rebuilt": page.rebuilt,
        "damage_map": [list(row) for row in page.damage_map],
    }
