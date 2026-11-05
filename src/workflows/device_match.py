from collections.abc import Sequence

from common.types import PrinterInfo, ScannerInfo


def matched_devices(
    printer_uri: str | None,
    scanner_id: str | None,
    printers: Sequence[PrinterInfo],
    scanners: Sequence[ScannerInfo],
) -> tuple[PrinterInfo | None, ScannerInfo | None]:
    printer = _find_printer(printers, printer_uri)
    scanner = _find_scanner(scanners, scanner_id)
    _require_known(printer_uri, printer, scanner_id, scanner)
    return printer, scanner


def _find_printer(printers: Sequence[PrinterInfo], uri: str | None) -> PrinterInfo | None:
    if uri is None:
        return None
    return next((item for item in printers if item.uri == uri), None)


def _find_scanner(scanners: Sequence[ScannerInfo], device_id: str | None) -> ScannerInfo | None:
    if device_id is None:
        return None
    return next((item for item in scanners if item.device_id == device_id), None)


def _require_known(
    printer_uri: str | None,
    printer: PrinterInfo | None,
    scanner_id: str | None,
    scanner: ScannerInfo | None,
) -> None:
    if printer_uri is not None and printer is None:
        raise ValueError(f"Unknown printer: {printer_uri}")
    if scanner_id is not None and scanner is None:
        raise ValueError(f"Unknown scanner: {scanner_id}")
