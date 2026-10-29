from __future__ import annotations

from common.device_config import get_scanner_settings
from common.device_discover import list_escl_scanners, saved_scanner_uri
from common.sane_discovery import get_scanner_capabilities, list_scanners
from common.types import ScannerCapabilities, ScannerInfo


def _scanner_label(s: ScannerInfo) -> str:
    if s.vendor or s.model:
        head = f"{s.vendor} {s.model}".strip()
        return f"{head} ({s.device_id})" if head else s.device_id
    return s.device_id


def discover_scanners_for_scan() -> tuple[list[tuple[str, str]], str | None]:
    scanners = [*list_escl_scanners(), *list_scanners()]
    saved = saved_scanner_uri() or str(get_scanner_settings().get("device", ""))
    options = [(_scanner_label(scanner), scanner.device_id) for scanner in scanners]
    if saved and any(scanner.device_id == saved for scanner in scanners):
        return options, saved
    return options, scanners[0].device_id if scanners else None


def resolve_max_dpi(device_id: str) -> int | None:
    if not device_id:
        return None
    if device_id.startswith(("http://", "https://")):
        return _escl_max_dpi(device_id)
    caps = get_scanner_capabilities(device_id)
    if caps is None:
        return None
    return _max_dpi_from_caps(caps)


def _escl_max_dpi(uri: str) -> int | None:
    from common.device_error import DeviceError
    from common.escl_scan import scanner_capabilities

    try:
        caps = scanner_capabilities(uri)
    except DeviceError:
        return None
    return max(caps.resolutions) if caps.resolutions else None


def _max_dpi_from_caps(caps: ScannerCapabilities) -> int | None:
    return max(caps.resolutions) if caps.resolutions else None


def label_for_device(
    options: list[tuple[str, str]],
    device_id: str | None,
) -> str:
    if not device_id:
        return ""
    for label, key in options:
        if key == device_id:
            return label
    return device_id
