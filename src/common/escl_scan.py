import logging
import time
from urllib.parse import urlsplit

from common.device_error import DeviceError
from common.escl_caps import ScannerCaps, parse_capabilities, scan_settings
from common.escl_http import request_escl

logger = logging.getLogger(__name__)


def scanner_capabilities(uri: str) -> ScannerCaps:
    status, _location, payload = request_escl(uri, "GET", "/eSCL/ScannerCapabilities", timeout=20)
    if status != 200:
        raise DeviceError(f"eSCL capabilities returned HTTP {status}")
    return parse_capabilities(payload)


def scan_jpeg(uri: str, dpi: int, timeout: float | None = None) -> tuple[bytes, int]:
    caps = scanner_capabilities(uri)
    settings = scan_settings(caps, dpi)
    status, location, payload = _submit_job(uri, settings)
    if status not in (200, 201) or not location:
        detail = payload[:180].decode("utf-8", "replace")
        raise DeviceError(f"eSCL scan job returned HTTP {status}: {detail}")
    job = _absolute(uri, location)
    chosen = _chosen_dpi(settings)
    try:
        image = _next_document(job, timeout or (45 if chosen <= 150 else 240))
    finally:
        _delete_job(job)
    logger.info("eSCL scan complete: %s dpi=%s bytes=%s", uri, chosen, len(image))
    return image, chosen


def _submit_job(uri: str, settings: bytes) -> tuple[int, str, bytes]:
    status, location, payload = 0, "", b""
    for attempt in range(6):
        status, location, payload = request_escl(
            uri, "POST", "/eSCL/ScanJobs", settings, timeout=30, content_type="text/xml; charset=utf-8",
        )
        if (status in (200, 201) and location) or status != 503:
            return status, location, payload
        logger.info("eSCL scanner busy (HTTP 503), attempt %s", attempt + 1)
        time.sleep(2)
    return status, location, payload


def _next_document(job: str, timeout: float) -> bytes:
    deadline = time.monotonic() + timeout
    target = job.rstrip("/") + "/NextDocument"
    while time.monotonic() < deadline:
        status, _location, payload = request_escl(_origin(target), "GET", urlsplit(target).path, timeout=timeout)
        if status == 200 and payload:
            return payload
        if status not in (404, 503):
            raise DeviceError(f"eSCL document returned HTTP {status}")
        time.sleep(1)
    raise DeviceError("eSCL scan did not produce a document")


def _delete_job(job: str) -> None:
    try:
        request_escl(_origin(job), "DELETE", urlsplit(job).path, timeout=10)
    except DeviceError as exc:
        logger.info("eSCL job cleanup failed: %s", exc)


def _absolute(base: str, location: str) -> str:
    if location.startswith(("http://", "https://")):
        return location
    parts = urlsplit(base)
    return f"{parts.scheme}://{parts.netloc}{location if location.startswith('/') else '/' + location}"


def _origin(uri: str) -> str:
    parts = urlsplit(uri)
    return f"{parts.scheme}://{parts.netloc}"


def _chosen_dpi(settings: bytes) -> int:
    text = settings.decode()
    start = text.find("<scan:XResolution>")
    end = text.find("</scan:XResolution>")
    if start < 0 or end < 0:
        return 0
    return int(text[start + len("<scan:XResolution>"):end])
