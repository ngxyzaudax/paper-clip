from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from common.sane_discovery import get_scanner_capabilities
from common.types import ScannerCapabilities

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ScanCaptureResult:
    target_path: Path
    dpi: int
    mode: str
    source: str


def _ensure_sane_module() -> "object":
    try:
        import sane
        sane.init()
        return sane
    except ImportError as exc:
        raise RuntimeError("python-sane not installed; scanner capture unavailable") from exc
    except Exception as exc:
        raise RuntimeError(f"SANE initialization failed: {exc}") from exc


def select_max_dpi(caps: ScannerCapabilities) -> int:
    if not caps.resolutions:
        raise RuntimeError("Scanner reports no resolutions")
    return max(caps.resolutions)


def select_default_mode(caps: ScannerCapabilities) -> str:
    preferred = ("Color", "color", "RGB", "rgb")
    for mode in preferred:
        if mode in caps.modes:
            return mode
    return caps.modes[0] if caps.modes else ""


def select_default_source(caps: ScannerCapabilities) -> str:
    preferred = ("Flatbed", "flatbed", "Platen")
    for src in preferred:
        if src in caps.sources:
            return src
    return caps.sources[0] if caps.sources else ""


def _set_option(device: object, name: str, value: object) -> None:
    try:
        setattr(device, name, value)
    except Exception as exc:
        logger.debug("Could not set %s=%s: %s", name, value, exc)


def _open_device(sane_module: object, device_id: str) -> object:
    try:
        return sane_module.open(device_id)
    except Exception as exc:
        raise RuntimeError(f"Failed to open scanner {device_id}: {exc}") from exc


def _scan_to_image(device: object) -> object:
    try:
        device.start()
        return device.snap()
    except Exception as exc:
        raise RuntimeError(f"Scan acquisition failed: {exc}") from exc


def _save_png(image: object, target_path: Path) -> None:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        image.save(str(target_path), format="PNG")
    except Exception as exc:
        raise RuntimeError(f"Failed to save scan to {target_path}: {exc}") from exc


def capture_scan(device_id: str, target_path: Path) -> ScanCaptureResult:
    if not device_id:
        raise ValueError("device_id is required")
    caps = get_scanner_capabilities(device_id)
    if caps is None:
        raise RuntimeError(f"Could not read capabilities for {device_id}")
    dpi = select_max_dpi(caps)
    mode = select_default_mode(caps)
    source = select_default_source(caps)
    sane_module = _ensure_sane_module()
    device = _open_device(sane_module, device_id)
    try:
        _set_option(device, "resolution", dpi)
        if mode:
            _set_option(device, "mode", mode)
        if source:
            _set_option(device, "source", source)
        image = _scan_to_image(device)
        _save_png(image, target_path)
    finally:
        try:
            device.close()
        except Exception:
            pass
    logger.info(
        "Scan captured: device=%s dpi=%s mode=%s source=%s -> %s",
        device_id, dpi, mode, source, target_path,
    )
    return ScanCaptureResult(target_path=target_path, dpi=dpi, mode=mode, source=source)
