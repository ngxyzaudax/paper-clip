from pathlib import Path

from common.cups_print import fallback_queue_uri, print_through_queue
from common.cups_queues import queue_name
from common.device_error import DeviceError
from common.ipp_client import printer_attributes, submit_document, validate_ticket, wait_for_job
from common.ipp_codec import IppMap
from common.ipp_duplex import require_duplex
from common.ipp_options import PrintTicket, build_ticket
from common.page_document import render_document, render_pages


def print_pages(
    uri: str,
    pages: list[Path],
    title: str,
    paper: str = "A4",
    duplex: bool = False,
) -> list[int]:
    if not pages:
        raise ValueError("no pages to print")
    if queue_name(uri):
        return [print_through_queue(uri, pages, title, duplex)]
    try:
        return _driverless_pages(uri, pages, title, paper, duplex)
    except DeviceError as exc:
        fallback = fallback_queue_uri(exc)
        if fallback is None:
            raise
        return [print_through_queue(fallback, pages, title, duplex)]


def _driverless_pages(
    uri: str,
    pages: list[Path],
    title: str,
    paper: str,
    duplex: bool,
) -> list[int]:
    attributes = printer_attributes(uri)
    if duplex:
        return _duplex_job(uri, pages, title, attributes, paper)
    return _one_sided_jobs(uri, pages, title, build_ticket(attributes, paper))


def _one_sided_jobs(uri: str, pages: list[Path], title: str, ticket: PrintTicket) -> list[int]:
    validate_ticket(uri, ticket)
    total = len(pages)
    return [
        _send(uri, render_document(page, ticket), _page_title(title, index, total), ticket)
        for index, page in enumerate(pages, start=1)
    ]


def _duplex_job(
    uri: str,
    pages: list[Path],
    title: str,
    attributes: IppMap,
    paper: str,
) -> list[int]:
    ticket = build_ticket(attributes, paper, require_duplex(attributes))
    validate_ticket(uri, ticket)
    return [_send(uri, render_pages(pages, ticket), title, ticket)]


def _send(uri: str, document: bytes, title: str, ticket: PrintTicket) -> int:
    job_id = submit_document(uri, ticket, document, title)
    wait_for_job(uri, job_id)
    return job_id


def _page_title(title: str, index: int, total: int) -> str:
    if total == 1:
        return title
    return f"{title} ({index}/{total})"
