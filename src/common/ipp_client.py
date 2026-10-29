import time

from common.device_error import DeviceError
from common.ipp_codec import IppMap, IppMessage, unpack_message
from common.ipp_http import post_ipp
from common.ipp_options import PrintTicket
from common.ipp_ticket import get_attributes_request, job_request, job_status_request

_OK = {0x0000, 0x0001, 0x0002}
_SAFETY = {"media", "media-col", "print-color-mode", "print-scaling", "sides", "printer-resolution"}
_FAILED_JOB = {7, 8}
_DONE_JOB = 9


def printer_attributes(uri: str, timeout: float = 20) -> IppMap:
    message = _exchange(uri, get_attributes_request(uri), timeout)
    return message.attributes


def validate_ticket(uri: str, ticket: PrintTicket) -> None:
    _exchange(uri, job_request(0x0004, uri, "paper-clip validate", ticket), 30)


def submit_document(uri: str, ticket: PrintTicket, document: bytes, title: str) -> int:
    message = _exchange(uri, job_request(0x0002, uri, title, ticket, document), 180)
    job_ids = message.attributes.get("job-id", [])
    if not job_ids or not isinstance(job_ids[0], int):
        raise DeviceError("printer accepted the job without a job id")
    return int(job_ids[0])


def wait_for_job(uri: str, job_id: int, timeout: float = 900) -> str:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        state = _job_state(uri, job_id)
        if state in _FAILED_JOB:
            raise DeviceError(f"print job {job_id} ended in state {state}")
        if state == _DONE_JOB:
            return "completed"
        time.sleep(2)
    raise DeviceError(f"print job {job_id} did not finish within {timeout:.0f}s")


def _job_state(uri: str, job_id: int) -> int:
    message = _exchange(uri, job_status_request(uri, job_id), 20)
    states = message.attributes.get("job-state", [])
    if not states or not isinstance(states[0], int):
        raise DeviceError(f"print job {job_id} did not report a state")
    return int(states[0])


def _exchange(uri: str, request: bytes, timeout: float) -> IppMessage:
    message = unpack_message(post_ipp(uri, request, timeout))
    if message.status not in _OK:
        raise DeviceError(f"IPP status {message.status:#06x} from {uri}")
    blocked = [name for name in message.unsupported if name in _SAFETY]
    if blocked:
        raise DeviceError("printer ignored required print options: " + ", ".join(blocked))
    return message
