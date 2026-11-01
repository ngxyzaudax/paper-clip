import logging
from collections.abc import Callable
from pathlib import Path
from typing import NamedTuple

from common.cups_print import fallback_queue_uri, print_through_queue
from common.cups_queues import queue_name
from common.device_error import DeviceError
from common.ipp_choices import choose_duplex
from common.ipp_client import printer_attributes, submit_document, validate_ticket, wait_for_job
from common.ipp_codec import IppMap
from common.ipp_duplex import printable_duplex
from common.ipp_options import build_ticket
from common.page_document import render_pages

logger = logging.getLogger(__name__)

_NO_DUPLEX = "This printer does not advertise duplex. Two sheets will be used."
_NO_DOCUMENT = "This printer cannot put both sides in one document. Two sheets will be used."


class SheetJob(NamedTuple):
    job_ids: list[int]
    sides: str
    sheets: int


def print_calibration_sheet(
    uri: str,
    front: Path,
    back: Path,
    notice: Callable[[str], None] | None = None,
) -> SheetJob:
    if queue_name(uri):
        return _queued_sheet(uri, front, back)
    try:
        return _direct_sheet(uri, front, back, notice)
    except DeviceError as exc:
        fallback = fallback_queue_uri(exc)
        if fallback is None:
            raise
        _tell(notice, "The printer address did not answer. Sending one duplex job through the Mac print queue.")
        return _queued_sheet(fallback, front, back)


def _direct_sheet(
    uri: str,
    front: Path,
    back: Path,
    notice: Callable[[str], None] | None,
) -> SheetJob:
    attributes = printer_attributes(uri)
    duplex = printable_duplex(attributes)
    if duplex is None:
        return _one_sided_sheets(uri, attributes, front, back, notice)
    logger.info("Printing calibration as one sheet with sides %s", duplex)
    job_id = _send(uri, attributes, [front, back], "paper-clip calibration", duplex)
    return SheetJob([job_id], duplex, 1)


def _queued_sheet(uri: str, front: Path, back: Path) -> SheetJob:
    job_id = print_through_queue(uri, [front, back], "paper-clip calibration", True)
    return SheetJob([job_id], "two-sided-long-edge", 1)


def _one_sided_sheets(
    uri: str,
    attributes: IppMap,
    front: Path,
    back: Path,
    notice: Callable[[str], None] | None,
) -> SheetJob:
    _tell(notice, _two_sheet_message(attributes))
    job_ids = [
        _send(uri, attributes, [front], "paper-clip calibration front", "one-sided"),
        _send(uri, attributes, [back], "paper-clip calibration back", "one-sided"),
    ]
    return SheetJob(job_ids, "one-sided", 2)


def _two_sheet_message(attributes: IppMap) -> str:
    if choose_duplex(attributes) is None:
        return _NO_DUPLEX
    return _NO_DOCUMENT


def _send(uri: str, attributes: IppMap, pages: list[Path], title: str, sides: str) -> int:
    ticket = build_ticket(attributes, "A4", sides)
    validate_ticket(uri, ticket)
    job_id = submit_document(uri, ticket, render_pages(pages, ticket), title)
    wait_for_job(uri, job_id)
    return job_id


def _tell(notice: Callable[[str], None] | None, message: str) -> None:
    logger.info("%s", message)
    if notice is not None:
        notice(message)
