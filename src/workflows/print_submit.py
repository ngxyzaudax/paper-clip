from common.data_store import record_print
from common.ipp_media import MEDIA_SIZES
from common.ipp_print import print_pages
from workflows.print_jobs import PrintJob


def submit_print_job(printer: str, job: PrintJob, duplex: bool) -> str:
    pages = list(job.page_paths)
    ids = print_pages(printer, pages, f"paper-clip {job.job_id}", require_paper(job.paper_size), duplex=duplex)
    _store(job, printer, duplex, ids)
    return _message(printer, len(pages), ids, duplex)


def require_paper(size: str) -> str:
    if size in MEDIA_SIZES:
        return size
    raise ValueError(f"Unknown paper size: {size}")


def _store(job: PrintJob, printer: str, duplex: bool, ids: list[int]) -> None:
    if job.job_dir is not None:
        record_print(job.job_dir, printer, duplex, ids)


def _message(printer: str, page_count: int, ids: list[int], duplex: bool) -> str:
    sides = " on both sides" if duplex else ""
    return f"Submitted {page_count} page(s){sides} to {printer}. Job IDs: {_ids(ids)}"


def _ids(ids: list[int]) -> str:
    return ", ".join(str(job_id) for job_id in ids)
