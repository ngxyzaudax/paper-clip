import json
import logging
from pathlib import Path

from common.data_store import DATA_ROOT
from common.device_config_types import DeviceConfigFile, PrinterSettings, ScannerSettings

logger = logging.getLogger(__name__)

CONFIG_DIR = DATA_ROOT
DEVICE_CONFIG_FILE = CONFIG_DIR / "devices.json"

EMPTY_PRINTER: PrinterSettings = {
    "name": "", "uri": "", "dpi": 0, "paper_size": "A4", "profile": {},
}
EMPTY_SCANNER: ScannerSettings = {
    "device": "", "uri": "", "dpi": 1200, "mode": "Color", "profile": {},
}


def load_device_config() -> DeviceConfigFile:
    parsed = _read_json(DEVICE_CONFIG_FILE) if DEVICE_CONFIG_FILE.exists() else None
    if parsed is None:
        return {"printer": dict(EMPTY_PRINTER), "scanner": dict(EMPTY_SCANNER)}
    try:
        return {"printer": _merge_printer(parsed.get("printer")), "scanner": _merge_scanner(parsed.get("scanner"))}
    except (TypeError, ValueError):
        return {"printer": dict(EMPTY_PRINTER), "scanner": dict(EMPTY_SCANNER)}


def save_device_config(config: DeviceConfigFile) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    DEVICE_CONFIG_FILE.write_text(json.dumps(config, indent=2) + "\n")
    logger.info("Device configuration saved to %s", DEVICE_CONFIG_FILE)


def save_printer_settings(
    name: str, uri: str = "", dpi: int = 0, paper_size: str = "A4",
) -> None:
    config = load_device_config()
    config["printer"] = {
        "name": name,
        "uri": uri,
        "dpi": dpi,
        "paper_size": paper_size,
        "profile": config["printer"].get("profile", {}),
    }
    save_device_config(config)


def save_scanner_settings(
    device: str, dpi: int = 1200, mode: str = "Color", uri: str = "",
) -> None:
    config = load_device_config()
    config["scanner"] = {
        "device": device,
        "uri": uri or _uri_from_device(device),
        "dpi": dpi,
        "mode": mode,
        "profile": config["scanner"].get("profile", {}),
    }
    save_device_config(config)


def get_printer_settings() -> PrinterSettings:
    return load_device_config()["printer"]


def get_scanner_settings() -> ScannerSettings:
    return load_device_config()["scanner"]


def _read_json(path: Path) -> dict[str, object] | None:
    try:
        raw = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    return raw if isinstance(raw, dict) else None


def _merge_printer(raw: object) -> PrinterSettings:
    merged = dict(EMPTY_PRINTER)
    if isinstance(raw, dict):
        merged["name"] = str(raw.get("name", merged["name"]))
        merged["uri"] = str(raw.get("uri", ""))
        merged["dpi"] = int(raw["dpi"]) if "dpi" in raw else merged["dpi"]
        merged["paper_size"] = str(raw.get("paper_size", merged["paper_size"]))
        merged["profile"] = _profile(raw.get("profile"))
    return merged


def _merge_scanner(raw: object) -> ScannerSettings:
    merged = dict(EMPTY_SCANNER)
    if isinstance(raw, dict):
        merged["device"] = str(raw.get("device", ""))
        merged["uri"] = str(raw.get("uri", "")) or _uri_from_device(merged["device"])
        merged["dpi"] = int(raw["dpi"]) if "dpi" in raw else merged["dpi"]
        merged["mode"] = str(raw.get("mode", merged["mode"]))
        merged["profile"] = _profile(raw.get("profile"))
    return merged


def _profile(raw: object) -> dict[str, str]:
    if not isinstance(raw, dict):
        return {}
    return {str(key): str(value) for key, value in raw.items() if isinstance(value, (str, int, float))}


def _uri_from_device(device: str) -> str:
    if device.startswith(("http://", "https://", "ipp://", "ipps://")):
        return device
    return ""
