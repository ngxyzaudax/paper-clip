from collections.abc import Sequence

from common.types import PrinterInfo, ScannerInfo
from workflows.print_jobs import PrintJob


def chosen_duplex(requested: bool | None, job: PrintJob) -> bool:
    if requested is None:
        return job.sides == 2
    return requested


def require_known_printer(printer: str, found: Sequence[PrinterInfo]) -> str:
    if not printer:
        raise ValueError("Choose a printer")
    if any(item.uri == printer for item in found):
        return printer
    raise ValueError(f"Unknown printer: {printer}")


def printer_rows(printers: Sequence[PrinterInfo]) -> list[dict[str, str]]:
    return [_printer_row(item) for item in printers]


def scanner_rows(scanners: Sequence[ScannerInfo]) -> list[dict[str, str]]:
    return [_scanner_row(item) for item in scanners]


def _printer_row(printer: PrinterInfo) -> dict[str, str]:
    return {"name": printer.name, "uri": printer.uri, "state": printer.state}


def _scanner_row(scanner: ScannerInfo) -> dict[str, str]:
    return {"device_id": scanner.device_id, "vendor": scanner.vendor, "model": scanner.model}
