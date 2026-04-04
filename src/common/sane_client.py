import logging
import subprocess

from PIL import Image

from common.sane_discovery import (
    _ensure_sane,
    get_scanner_capabilities,
    list_scanners,
)

logger = logging.getLogger(__name__)

__all__ = ["list_scanners", "get_scanner_capabilities", "scan_page"]


def scan_page(
    device_id: str,
    dpi: int = 1200,
    mode: str = "Color",
) -> Image.Image | None:
    if not _ensure_sane():
        return _scan_page_fallback(device_id, dpi, mode)
    try:
        import sane
        device = sane.open(device_id)
        try:
            device.resolution = dpi
            device.mode = mode
            device.start()
            image = device.snap()
        finally:
            device.close()
        return image
    except Exception as exc:
        logger.warning("SANE scan failed, trying scanimage fallback: %s", exc)
        return _scan_page_fallback(device_id, dpi, mode)


def _scan_page_fallback(
    device_id: str, dpi: int, mode: str,
) -> Image.Image | None:
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        result = subprocess.run(
            [
                "scanimage", "-d", device_id,
                "--mode", mode,
                "--resolution", str(dpi),
                "--format=png",
                f"--output-file={tmp_path}",
            ],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0:
            logger.error("scanimage fallback failed: %s", result.stderr.strip())
            return None
        return Image.open(tmp_path).copy()
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        logger.error("scanimage fallback unavailable: %s", exc)
        return None
    finally:
        import os
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
