from pathlib import Path

from common.ipp_client import printer_attributes, submit_document, validate_ticket, wait_for_job
from common.ipp_options import build_ticket
from common.page_document import render_document


def print_pages(uri: str, pages: list[Path], title: str, paper: str = "A4") -> list[int]:
    if not pages:
        raise ValueError("no pages to print")
    ticket = build_ticket(printer_attributes(uri), paper)
    validate_ticket(uri, ticket)
    job_ids: list[int] = []
    total = len(pages)
    for index, page in enumerate(pages, start=1):
        job_title = title if total == 1 else f"{title} ({index}/{total})"
        job_id = submit_document(uri, ticket, render_document(page, ticket), job_title)
        wait_for_job(uri, job_id)
        job_ids.append(job_id)
    return job_ids
