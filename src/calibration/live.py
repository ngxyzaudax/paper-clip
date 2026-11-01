from collections.abc import Callable
from pathlib import Path

import numpy as np

from calibration.print_sheet import print_calibration_sheet
from common.device_config import get_printer_settings, get_scanner_settings
from common.device_discover import list_escl_scanners, list_ipp_printers
from common.device_error import DeviceError
from common.scan_capture import capture_page
from serialization.decode.load_scan import load_scans


def print_and_scan(
    front: Path,
    back: Path,
    scan_dir: Path,
    scan_dpi: int,
    notice: Callable[[str], None] | None = None,
) -> list[np.ndarray]:
    printer = _printer_uri()
    scanner = _scanner_uri()
    print_calibration_sheet(printer, front, back, notice)
    scan_dir.mkdir(parents=True, exist_ok=True)
    capture_page(scanner, scan_dir / "front.png", scan_dpi)
    capture_page(scanner, scan_dir / "back.png", scan_dpi)
    return [image for path in (scan_dir / "front.png", scan_dir / "back.png") for image in load_scans(path)]


def _printer_uri() -> str:
    saved = str(get_printer_settings().get("uri", ""))
    if saved:
        return saved
    found = list_ipp_printers()
    if len(found) == 1:
        return found[0].uri
    if not found:
        raise DeviceError("no IPP printer found")
    listed = ", ".join(item.uri for item in found)
    raise DeviceError(f"multiple printers; set printer.uri ({listed})")


def _scanner_uri() -> str:
    saved = str(get_scanner_settings().get("uri", ""))
    if saved:
        return saved
    found = list_escl_scanners()
    if len(found) == 1:
        return found[0].device_id
    if not found:
        raise DeviceError("no eSCL scanner found")
    listed = ", ".join(item.device_id for item in found)
    raise DeviceError(f"multiple scanners; set scanner.uri ({listed})")
