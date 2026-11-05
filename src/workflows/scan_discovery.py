import logging
from collections.abc import Sequence

from common.device_config import get_scanner_settings
from common.device_discover import list_escl_scanners, saved_scanner_uri
from common.device_error import DeviceError
from common.escl_caps import ScannerCaps
from common.sane_discovery import get_scanner_capabilities, list_scanners
from common.types import ScannerInfo

logger = logging.getLogger(__name__)


def scanner_catalog() -> tuple[list[ScannerInfo], str | None]:
    scanners = [*list_escl_scanners(), *list_scanners()]
    return scanners, _selected(scanners, _saved_id())


def discover_scanners_for_scan() -> tuple[list[tuple[str, str]], str | None]:
    scanners, selected = scanner_catalog()
    return [_option(scanner) for scanner in scanners], selected


def resolve_max_dpi(device_id: str) -> int | None:
    if not device_id:
        return None
    if is_escl_device(device_id):
        return _escl_max_dpi(device_id)
    return _sane_max_dpi(device_id)


def is_escl_device(device_id: str) -> bool:
    return device_id.startswith(("http://", "https://"))


def read_escl_caps(uri: str) -> ScannerCaps:
    from common.escl_scan import scanner_capabilities

    return scanner_capabilities(uri)


def _saved_id() -> str:
    return saved_scanner_uri() or str(get_scanner_settings().get("device", ""))


def _selected(scanners: Sequence[ScannerInfo], saved: str) -> str | None:
    if any(scanner.device_id == saved for scanner in scanners):
        return saved
    if not scanners:
        return None
    return scanners[0].device_id


def _option(scanner: ScannerInfo) -> tuple[str, str]:
    return _label(scanner), scanner.device_id


def _label(scanner: ScannerInfo) -> str:
    head = f"{scanner.vendor} {scanner.model}".strip()
    if head:
        return f"{head} ({scanner.device_id})"
    return scanner.device_id


def _escl_max_dpi(uri: str) -> int | None:
    try:
        caps = read_escl_caps(uri)
    except DeviceError as exc:
        logger.warning("Scanner capabilities failed for %s: %s", uri, exc)
        raise DeviceError("The scanner did not answer. Check that it is turned on and on this network, then try again.") from exc
    return _peak(caps.resolutions)


def _sane_max_dpi(device_id: str) -> int | None:
    caps = get_scanner_capabilities(device_id)
    if caps is None:
        return None
    return _peak(caps.resolutions)


def _peak(resolutions: Sequence[int]) -> int | None:
    if not resolutions:
        return None
    return max(resolutions)
