import logging
from collections.abc import Callable

from fastapi import APIRouter, HTTPException

from common.device_error import DeviceError
from web.device_rows import chosen_duplex, printer_rows, require_known_printer
from web.present import print_summary
from web.request_models import PrintRequest
from web.tasks import TaskRecord, submit
from workflows.devices import discover_printers
from workflows.print_jobs import PrintJob, discover_print_jobs, job_by_id
from workflows.print_submit import require_paper, submit_print_job

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/print/jobs")
def print_jobs() -> list[dict[str, object]]:
    return [print_summary(job) for job in discover_print_jobs()]


@router.get("/print/jobs/{job_id}")
def print_job(job_id: str) -> dict[str, object]:
    return print_summary(_require_job(job_id))


@router.get("/print/printers")
def printers() -> dict[str, object]:
    found, selected = discover_printers()
    return {"printers": printer_rows(found), "selected": selected}


@router.post("/print/jobs/{job_id}")
def print_submit(job_id: str, body: PrintRequest) -> dict[str, str]:
    _require_confirm(body.confirm)
    job = _require_job(job_id)
    printer = require_known_printer(body.printer, discover_printers()[0])
    require_paper(job.paper_size)
    return {"task_id": submit(_print_task(printer, job, chosen_duplex(body.duplex, job)))}


def _require_confirm(confirm: bool) -> None:
    if confirm is not True:
        raise HTTPException(400, "confirm is required")


def _require_job(job_id: str) -> PrintJob:
    job = job_by_id(job_id)
    if job is None:
        raise HTTPException(404, "Print job not found")
    return job


def _print_task(printer: str, job: PrintJob, duplex: bool) -> Callable[[TaskRecord], dict[str, object]]:
    def run(record: TaskRecord) -> dict[str, object]:
        return _print_result(printer, job, duplex, record)
    return run


def _print_result(printer: str, job: PrintJob, duplex: bool, record: TaskRecord) -> dict[str, object]:
    logger.info("Print task %s is submitting job %s", record.id, job.job_id)
    return {"message": _submitted(printer, job, duplex)}


def _submitted(printer: str, job: PrintJob, duplex: bool) -> str:
    try:
        return submit_print_job(printer, job, duplex)
    except DeviceError as exc:
        raise ValueError(str(exc)) from exc
