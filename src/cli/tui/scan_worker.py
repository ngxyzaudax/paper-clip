from __future__ import annotations

from common.device_config import get_scanner_settings
from common.sane_discovery import get_scanner_capabilities, list_scanners
from common.types import ScannerCapabilities, ScannerInfo


def _scanner_label(s: ScannerInfo) -> str:
    if s.vendor or s.model:
        head = f"{s.vendor} {s.model}".strip()
        return f"{head} ({s.device_id})" if head else s.device_id
    return s.device_id


def discover_scanners_for_scan() -> tuple[list[tuple[str, str]], str | None]:
    scanners = list_scanners()
    saved = get_scanner_settings().get("device", "")
    options = [(_scanner_label(s), s.device_id) for s in scanners]
    initial: str | None = None
    if saved and any(s.device_id == saved for s in scanners):
        initial = saved
    elif scanners:
        initial = scanners[0].device_id
    return options, initial


def resolve_max_dpi(device_id: str) -> int | None:
    if not device_id:
        return None
    caps = get_scanner_capabilities(device_id)
    if caps is None:
        return None
    return _max_dpi_from_caps(caps)


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
