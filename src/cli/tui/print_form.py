from typing import NamedTuple

from cli.tui.devices_worker import discover_printers
from cli.tui.print_jobs import PrintJob, discover_print_jobs, job_option_label
from common.device_config import get_printer_settings
from common.ipp_media import MEDIA_SIZES
from common.ipp_print import print_pages
from common.types import PrinterInfo


class PrintForm(NamedTuple):
    printers: list[PrinterInfo]
    jobs: list[PrintJob]
    printer_options: list[tuple[str, str]]
    job_options: list[tuple[str, str]]
    printer_name: str | None
    job_id: str | None


def load_print_form() -> PrintForm:
    printers: list[PrinterInfo] = []
    printer_options, printer_name = discover_printers(printers)
    jobs = discover_print_jobs()
    saved_printer = str(get_printer_settings().get("uri", ""))
    job_options = [(job_option_label(job), job.job_id) for job in jobs]
    job_id = job_options[0][1] if job_options else None
    return PrintForm(
        printers,
        jobs,
        printer_options,
        job_options,
        _saved_printer(printer_options, printer_name, saved_printer),
        job_id,
    )


def _saved_printer(
    options: list[tuple[str, str]],
    printer_name: str | None,
    saved_printer: str,
) -> str | None:
    if saved_printer and any(uri == saved_printer for _, uri in options):
        return saved_printer
    return printer_name


def submit_print_job(printer: str, job: PrintJob, duplex: bool) -> str:
    paper = job.paper_size if job.paper_size in MEDIA_SIZES else "A4"
    pages = list(job.page_paths)
    ids = print_pages(printer, pages, f"paper-clip {job.job_id}", paper, duplex=duplex)
    return _submitted(printer, len(pages), ids, duplex)


def _submitted(printer: str, page_count: int, ids: list[int], duplex: bool) -> str:
    ids_text = ", ".join(str(job_id) for job_id in ids)
    if duplex:
        return (
            f"[bold green]Submitted {page_count} page(s) on both sides to {printer}. "
            f"Job IDs: {ids_text}[/bold green]"
        )
    return f"[bold green]Submitted {len(ids)} page(s) to {printer}. Job IDs: {ids_text}[/bold green]"
