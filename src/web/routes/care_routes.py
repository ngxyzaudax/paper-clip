import logging
from collections.abc import Callable
from pathlib import Path

from fastapi import APIRouter, HTTPException

from health.check import run_check
from health.store import all_tracked, find_tracked, forget_tracked, load_tracked
from web.device_payload import device_payload, paper_setting, saved_scanner_dpi
from web.present import health_detail, health_row
from web.request_models import DeviceSelection, HealthCheck
from web.tasks import TaskRecord, submit
from workflows.device_match import matched_devices
from workflows.devices import discover_printers, discover_scanners, printer_ticket, save_defaults, scanner_caps
from workflows.scan_list import discover_scan_jobs

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
def health_list() -> list[dict[str, object]]:
    return [health_row(item) for item in all_tracked()]


@router.get("/health/{sha}")
def health_one(sha: str) -> dict[str, object]:
    item = find_tracked(sha) or load_tracked(sha)
    if item is None:
        raise HTTPException(404, "No health history for that file")
    return health_detail(item)


@router.delete("/health/{sha}")
def health_forget(sha: str, confirm: bool = False) -> dict[str, str]:
    if not confirm:
        raise HTTPException(400, "confirm is required")
    item = find_tracked(sha)
    if item is None:
        raise HTTPException(404, "No health history for that file")
    forget_tracked(item.sha256)
    return {"message": "Forgotten"}


@router.post("/health/check")
def health_check(body: HealthCheck) -> dict[str, str]:
    return {"task_id": submit(_health_task(_scan_folder(body.scan_job_id)))}


@router.get("/devices")
def devices() -> dict[str, object]:
    printers, printer_uri = discover_printers()
    scanners, scanner_id = discover_scanners()
    return device_payload(printers, printer_uri, scanners, scanner_id)


@router.get("/devices/printer")
def device_printer(uri: str) -> dict[str, object]:
    return printer_ticket(uri, paper_setting())


@router.get("/devices/scanner")
def device_scanner(device: str) -> dict[str, object]:
    return scanner_caps(device)


@router.post("/devices")
def save_devices(body: DeviceSelection) -> dict[str, str]:
    printer, scanner = matched_devices(body.printer_uri, body.scanner_id, discover_printers()[0], discover_scanners()[0])
    save_defaults(printer, scanner, saved_scanner_dpi())
    return {"message": "Saved defaults"}


def _scan_folder(job_id: str) -> Path:
    folder = next((job.folder for job in discover_scan_jobs(include_empty=True) if job.job_id == job_id), None)
    if folder is None:
        raise HTTPException(404, "Scan session not found")
    return folder


def _health_task(folder: Path) -> Callable[[TaskRecord], dict[str, object]]:
    def run(record: TaskRecord) -> dict[str, object]:
        return _health_result(folder, record)
    return run


def _health_result(folder: Path, record: TaskRecord) -> dict[str, object]:
    logger.info("Health task %s is checking %s", record.id, folder.name)
    check = run_check(folder, track=True)
    return {"message": f"Health {check.reading.report.health:.1f}%", "sha256": check.sha256}
