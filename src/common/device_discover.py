import time
from urllib.parse import urlsplit

from common.device_config import get_printer_settings, get_scanner_settings
from common.mdns_browse import browse_types
from common.mdns_parse import Service
from common.device_uri import printer_from_service, scanner_from_service
from common.types import PrinterInfo, ScannerInfo

_CACHE: tuple[float, dict[str, list[Service]]] | None = None


def list_ipp_printers(timeout: float = 1.6) -> list[PrinterInfo]:
    saved = str(get_printer_settings().get("uri", ""))
    services = _prefer_plain_ipp(
        _services("_ipp._tcp.local", timeout) + _services("_ipps._tcp.local", timeout),
    )
    found = [printer_from_service(service, saved) for service in services]
    return _include_printer(found, saved)


def list_escl_scanners(timeout: float = 1.6) -> list[ScannerInfo]:
    saved = saved_scanner_uri()
    found = [scanner_from_service(service, saved) for service in _services("_uscan._tcp.local", timeout)]
    return _include_scanner(found, saved)


def saved_scanner_uri() -> str:
    settings = get_scanner_settings()
    uri = str(settings.get("uri", ""))
    if uri:
        return uri
    device = str(settings.get("device", ""))
    if device.startswith(("http://", "https://")):
        return device
    return ""


def _services(service_type: str, timeout: float) -> list[Service]:
    return _browse(timeout).get(service_type, [])


def _browse(timeout: float) -> dict[str, list[Service]]:
    global _CACHE
    now = time.monotonic()
    if _CACHE is not None and now - _CACHE[0] < 8:
        return _CACHE[1]
    found = browse_types(timeout=timeout)
    _CACHE = (now, found)
    return found


def _prefer_plain_ipp(services: list[Service]) -> list[Service]:
    chosen: dict[str, Service] = {}
    for service in services:
        key = (service.txt.get("UUID") or service.instance).lower()
        current = chosen.get(key)
        if current is None or (_plain(service) and not _plain(current)):
            chosen[key] = service
    return list(chosen.values())


def _plain(service: Service) -> bool:
    return service.service_type.lower().startswith("_ipp._")


def _include_printer(found: list[PrinterInfo], saved: str) -> list[PrinterInfo]:
    if not saved or any(item.uri == saved for item in found):
        return found
    host = urlsplit(saved).hostname or saved
    return [PrinterInfo(host, saved, "configured", True), *found]


def _include_scanner(found: list[ScannerInfo], saved: str) -> list[ScannerInfo]:
    if not saved or any(item.device_id == saved for item in found):
        return found
    host = urlsplit(saved).hostname or saved
    return [ScannerInfo(saved, "", host, "escl"), *found]
