import logging
import shutil
import tempfile
from pathlib import Path

from common.cups_job import submit_queue_job, wait_for_queue_job
from common.cups_pdf import write_page_pdf
from common.cups_queues import only_queue, queue_name, queue_uri
from common.device_error import DeviceError

logger = logging.getLogger(__name__)


def unreachable(exc: BaseException) -> bool:
    text = str(exc).lower()
    return "ipp request" in text and "failed" in text


def fallback_queue_uri(exc: BaseException) -> str | None:
    queue = only_queue() if unreachable(exc) else None
    if queue is None:
        return None
    logger.info("Printer did not answer (%s). Using print queue %s.", exc, queue.name)
    return queue_uri(queue.name)


def print_through_queue(uri: str, pages: list[Path], title: str, duplex: bool) -> int:
    queue = queue_name(uri)
    if queue is None:
        raise DeviceError(f"not a local print queue: {uri}")
    directory = Path(tempfile.mkdtemp(prefix="paper-clip-print-"))
    pdf = directory / "pages.pdf"
    try:
        write_page_pdf(pages, pdf)
        job_id = submit_queue_job(queue, pdf, title, duplex)
        wait_for_queue_job(queue, job_id)
        return job_id
    finally:
        shutil.rmtree(directory, ignore_errors=True)
