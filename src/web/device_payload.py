import logging
from collections.abc import Callable

from common.device_config import get_printer_settings, get_scanner_settings
from common.device_error import DeviceError
from common.spoken_error import plain_device_message
from common.types import PrinterInfo, ScannerInfo
from web.device_rows import printer_rows, scanner_rows
from workflows.devices import printer_ticket, scanner_caps

logger = logging.getLogger(__name__)


def device_payload(
    printers: list[PrinterInfo],
    printer_uri: str | None,
    scanners: list[ScannerInfo],
    scanner_id: str | None,
) -> dict[str, object]:
    return {
        "printers": printer_rows(printers),
        "scanners": scanner_rows(scanners),
        "printer_uri": printer_uri or "",
        "scanner_id": scanner_id or "",
        "printer_caps": _printer_caps(printer_uri),
        "scanner_caps": _scanner_caps(scanner_id),
    }


def paper_setting() -> str:
    return str(get_printer_settings().get("paper_size") or "A4")


def saved_scanner_dpi() -> int:
    return int(get_scanner_settings().get("dpi", 0) or 1200)


def _printer_caps(printer_uri: str | None) -> dict[str, object]:
    if not printer_uri:
        return {}
    return _caps(lambda: printer_ticket(printer_uri, paper_setting()))


def _scanner_caps(scanner_id: str | None) -> dict[str, object]:
    if not scanner_id:
        return {}
    return _caps(lambda: scanner_caps(scanner_id))


def _caps(read: Callable[[], dict[str, object]]) -> dict[str, object]:
    try:
        return read()
    except (ValueError, DeviceError) as exc:
        logger.warning("Device capabilities failed: %s", exc)
        return {"error": plain_device_message(str(exc))}
