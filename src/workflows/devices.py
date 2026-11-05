from common.device_config import (
    get_printer_settings,
    get_scanner_settings,
    save_printer_settings,
    save_scanner_settings,
)
from common.device_config_types import ScannerSettings
from common.device_discover import list_ipp_printers
from common.device_error import DeviceError
from common.escl_caps import ScannerCaps
from common.ipp_options import PrintTicket
from common.types import PrinterInfo, ScannerInfo
from workflows.scan_discovery import is_escl_device, read_escl_caps, scanner_catalog


def discover_printers() -> tuple[list[PrinterInfo], str | None]:
    printers = list_ipp_printers()
    saved = str(get_printer_settings().get("uri", ""))
    initial = saved if any(printer.uri == saved for printer in printers) else None
    if initial is None and printers:
        initial = printers[0].uri
    return printers, initial


def discover_scanners() -> tuple[list[ScannerInfo], str | None]:
    return scanner_catalog()


def printer_ticket(printer_uri: str, paper: str) -> dict[str, object]:
    return _ticket_body(printer_uri, _ticket(printer_uri, paper))


def scanner_caps(device_id: str) -> dict[str, object]:
    if is_escl_device(device_id):
        return _escl_caps(device_id)
    return _sane_caps(device_id)


def save_defaults(printer: PrinterInfo | None, scanner: ScannerInfo | None, dpi: int) -> None:
    _save_printer(printer)
    _save_scanner(scanner, dpi)


def _ticket(printer_uri: str, paper: str) -> PrintTicket:
    try:
        return _build_ticket(printer_uri, paper)
    except DeviceError as exc:
        raise ValueError(str(exc)) from exc


def _build_ticket(printer_uri: str, paper: str) -> PrintTicket:
    from common.ipp_client import printer_attributes
    from common.ipp_options import build_ticket

    return build_ticket(printer_attributes(printer_uri), paper)


def _ticket_body(printer_uri: str, ticket: PrintTicket) -> dict[str, object]:
    return {
        "uri": printer_uri,
        "document_format": ticket.document_format,
        "dpi": ticket.dpi,
        "media": ticket.media.keyword,
        "source": ticket.source,
        "margin_mm": ticket.margin / 100,
        "color": ticket.color,
        "quality": ticket.quality,
        "scaling": ticket.scaling,
        "sides": ticket.sides,
    }


def _escl_caps(uri: str) -> dict[str, object]:
    try:
        return _escl_body(uri, read_escl_caps(uri))
    except DeviceError as exc:
        raise ValueError(str(exc)) from exc


def _escl_body(uri: str, caps: ScannerCaps) -> dict[str, object]:
    return {"uri": uri, "resolutions": list(caps.resolutions), "modes": list(caps.color_modes), "source": caps.source}


def _sane_caps(device_id: str) -> dict[str, object]:
    from common.sane_discovery import get_scanner_capabilities

    caps = get_scanner_capabilities(device_id)
    if caps is None:
        raise ValueError(f"Could not read capabilities for {device_id}")
    return _sane_body(device_id, list(caps.resolutions), list(caps.modes), list(caps.sources))


def _sane_body(device_id: str, resolutions: list[int], modes: list[str], sources: list[str]) -> dict[str, object]:
    return {"device": device_id, "resolutions": resolutions, "modes": modes, "sources": sources}


def _save_printer(printer: PrinterInfo | None) -> None:
    if printer is not None:
        save_printer_settings(printer.name, printer.uri)


def _save_scanner(scanner: ScannerInfo | None, dpi: int) -> None:
    if scanner is None:
        return
    current = get_scanner_settings()
    save_scanner_settings(scanner.device_id, _dpi(dpi, current), str(current.get("mode") or "Color"), _network_uri(scanner))


def _dpi(dpi: int, current: ScannerSettings) -> int:
    return dpi or int(current.get("dpi", 0) or 1200)


def _network_uri(scanner: ScannerInfo) -> str:
    if is_escl_device(scanner.device_id):
        return scanner.device_id
    return ""
