import logging
import socket
import sys
from collections.abc import Callable, Mapping, Sequence
from urllib.parse import urlsplit

from common.device_config import get_printer_settings, get_scanner_settings
from common.device_discover import last_uscan_services, list_escl_scanners, list_ipp_printers, saved_scanner_uri
from common.device_error import DeviceError
from common.sane_discovery import list_scanners
from common.types import PrinterInfo, ScannerInfo
from workflows.scan_discovery import is_escl_device, resolve_max_dpi

logger = logging.getLogger(__name__)


def choose_printer(settings: Mapping[str, object], load: Callable[[], Sequence[PrinterInfo]]) -> str:
    saved = str(settings.get("uri", ""))
    if saved:
        return saved
    return _single_printer(tuple(load()))


def saved_or_only_printer() -> str:
    return choose_printer(get_printer_settings(), _discovered_printers)


def scanner_to_use(explicit: str | None = None) -> str:
    if explicit:
        return explicit
    chosen = _reachable(_saved_or_discovered())
    logger.info("Calibration scanner is %s", chosen)
    return chosen


def dpi_to_use(device_id: str, explicit: int | None = None) -> int:
    chosen = explicit if explicit is not None else _maximum_or_saved(device_id)
    logger.info("Calibration scan resolution is %s dpi", chosen)
    return chosen


def _discovered_printers() -> list[PrinterInfo]:
    return list_ipp_printers()


def _single_printer(found: tuple[PrinterInfo, ...]) -> str:
    if len(found) == 1:
        return found[0].uri
    if not found:
        raise DeviceError("no IPP printer found; pass --uri or set printer.uri")
    raise DeviceError(f"multiple IPP printers; pass --uri ({_uris(found)})")


def _uris(found: Sequence[PrinterInfo]) -> str:
    return ", ".join(item.uri for item in found)


def _maximum_or_saved(device_id: str) -> int:
    found = resolve_max_dpi(device_id)
    if found:
        return found
    saved = int(get_scanner_settings().get("dpi", 0) or 0)
    return saved or 1200


def _saved_or_discovered() -> str:
    saved = saved_scanner_uri() or _saved_device()
    if saved:
        return saved
    found = [*list_escl_scanners(), *list_scanners()]
    if len(found) == 1:
        return found[0].device_id
    return _missing(found)


def _saved_device() -> str:
    device = str(get_scanner_settings().get("device", ""))
    if is_escl_device(device):
        return ""
    return device


def _missing(found: list[ScannerInfo]) -> str:
    if not found:
        raise DeviceError("no scanner found; pass --uri or set scanner.uri")
    listed = ", ".join(item.device_id for item in found)
    raise DeviceError(f"multiple scanners; pass --uri ({listed})")


def _reachable(uri: str) -> str:
    named = _local_uri(uri)
    if named == uri:
        return uri
    if _tcp_open(named):
        return named
    if _tcp_open(uri):
        return uri
    return named


def _local_uri(uri: str) -> str:
    if sys.platform != "darwin":
        return uri
    parts = urlsplit(uri)
    host = _local_name(parts.hostname or "")
    if not host:
        return uri
    port = parts.port or (443 if parts.scheme == "https" else 80)
    return f"{parts.scheme}://{host}:{port}"


def _local_name(ip: str) -> str:
    if not _ipv4(ip):
        return ""
    for service in last_uscan_services():
        host = service.host.rstrip(".")
        if ip in service.addresses and host and not _ipv4(host):
            return host
    return ""


def _ipv4(host: str) -> bool:
    pieces = host.split(".")
    if len(pieces) != 4:
        return False
    return all(piece.isdigit() and 0 <= int(piece) <= 255 for piece in pieces)


def _tcp_open(uri: str) -> bool:
    parts = urlsplit(uri)
    host = parts.hostname or ""
    port = parts.port or (443 if parts.scheme == "https" else 80)
    try:
        with socket.create_connection((host, port), timeout=3):
            return True
    except OSError as exc:
        logger.info("Scanner %s:%s is not reachable: %s", host, port, exc)
        return False
