import io
from pathlib import Path

from PIL import Image

from common.escl_scan import scan_jpeg
from common.sane_scan import ScanCaptureResult


def capture_page(device_id: str, target: Path, dpi: int | None = None) -> ScanCaptureResult:
    if device_id.startswith(("http://", "https://")):
        return _capture_escl(device_id, target, dpi or 1200)
    from common.sane_scan import capture_scan

    return capture_scan(device_id, target)


def _capture_escl(uri: str, target: Path, dpi: int) -> ScanCaptureResult:
    payload, used = scan_jpeg(uri, dpi)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.suffix.lower() == ".png":
        Image.open(io.BytesIO(payload)).convert("RGB").save(target, format="PNG")
    else:
        target.write_bytes(payload)
    return ScanCaptureResult(target_path=target, dpi=used, mode="Color", source="Platen")
