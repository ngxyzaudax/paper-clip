import logging
import subprocess

from common.types import ScannerCapabilities, ScannerInfo

logger = logging.getLogger(__name__)


def _ensure_sane() -> bool:
    global _sane_initialized
    if _sane_initialized:
        return True
    try:
        import sane
        sane.init()
        _sane_initialized = True
        return True
    except ImportError:
        logger.warning("python-sane not installed; scanner discovery unavailable")
        return False
    except Exception as exc:
        logger.warning("SANE initialization failed: %s", exc)
        return False


_sane_initialized = False


def list_scanners() -> list[ScannerInfo]:
    if not _ensure_sane():
        return _list_scanners_fallback()
    try:
        import sane
        devices = sane.get_devices()
        return [
            ScannerInfo(
                device_id=dev[0],
                vendor=dev[1],
                model=dev[2],
                device_type=dev[3],
            )
            for dev in devices
        ]
    except Exception as exc:
        logger.warning("SANE device enumeration failed: %s", exc)
        return _list_scanners_fallback()


def _list_scanners_fallback() -> list[ScannerInfo]:
    try:
        result = subprocess.run(
            ["scanimage", "--list-devices"],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode != 0:
            return []
        scanners: list[ScannerInfo] = []
        for line in result.stdout.strip().splitlines():
            if "`" in line and "'" in line:
                device_id = line.split("`")[1].split("'")[0]
                rest = line.split("'", 1)[-1].strip() if "'" in line else ""
                scanners.append(ScannerInfo(
                    device_id=device_id,
                    vendor="",
                    model=rest or device_id,
                    device_type="scanner",
                ))
        return scanners
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []


def _read_option_constraint(device: "sane.SaneDev", option_name: str) -> list[str]:
    try:
        opts = {o[1]: o for o in device.get_options() if len(o) > 1}
        if option_name not in opts:
            return []
        info = opts[option_name]
        constraint = info[8] if len(info) > 8 else None
        if constraint is None:
            return []
        if isinstance(constraint, list):
            return [str(v) for v in constraint]
        if isinstance(constraint, tuple) and len(constraint) == 3:
            lo, hi, step = constraint
            step = max(step, 1)
            return [str(v) for v in range(int(lo), int(hi) + 1, int(step))]
        return []
    except Exception:
        return []


def get_scanner_capabilities(device_id: str) -> ScannerCapabilities | None:
    if not _ensure_sane():
        return None
    try:
        import sane
        device = sane.open(device_id)
        try:
            raw_resolutions = _read_option_constraint(device, "resolution")
            resolutions = sorted({int(float(r)) for r in raw_resolutions if r.replace(".", "").isdigit()})
            modes = _read_option_constraint(device, "mode")
            sources = _read_option_constraint(device, "source")
        finally:
            device.close()
        return ScannerCapabilities(
            resolutions=resolutions,
            modes=modes,
            sources=sources,
        )
    except Exception as exc:
        logger.warning("Failed to read capabilities for %s: %s", device_id, exc)
        return None
