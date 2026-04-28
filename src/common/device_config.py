import json
import logging
from pathlib import Path
from common.data_store import DATA_ROOT
from common.device_config_types import DeviceConfigFile, PrinterSettings, ScannerSettings

logger = logging.getLogger(__name__)

CONFIG_DIR = DATA_ROOT
DEVICE_CONFIG_FILE = CONFIG_DIR / "devices.json"

EMPTY_PRINTER: PrinterSettings = {"name": "", "dpi": 0, "paper_size": "A4"}
EMPTY_SCANNER: ScannerSettings = {"device": "", "dpi": 1200, "mode": "Color"}


def _merge_printer(raw: object) -> PrinterSettings:
    name, dpi, paper_size = EMPTY_PRINTER["name"], EMPTY_PRINTER["dpi"], EMPTY_PRINTER["paper_size"]
    if isinstance(raw, dict):
        if "name" in raw:
            name = str(raw["name"])
        if "dpi" in raw:
            dpi = int(raw["dpi"])
        if "paper_size" in raw:
            paper_size = str(raw["paper_size"])
    return {"name": name, "dpi": dpi, "paper_size": paper_size}


def _merge_scanner(raw: object) -> ScannerSettings:
    device, dpi, mode = EMPTY_SCANNER["device"], EMPTY_SCANNER["dpi"], EMPTY_SCANNER["mode"]
    if isinstance(raw, dict):
        if "device" in raw:
            device = str(raw["device"])
        if "dpi" in raw:
            dpi = int(raw["dpi"])
        if "mode" in raw:
            mode = str(raw["mode"])
    return {"device": device, "dpi": dpi, "mode": mode}


def load_device_config() -> DeviceConfigFile:
    if DEVICE_CONFIG_FILE.exists():
        try:
            raw = json.loads(DEVICE_CONFIG_FILE.read_text())
            if not isinstance(raw, dict):
                raise ValueError("invalid root")
            return {
                "printer": _merge_printer(raw.get("printer")),
                "scanner": _merge_scanner(raw.get("scanner")),
            }
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            pass
    return {"printer": dict(EMPTY_PRINTER), "scanner": dict(EMPTY_SCANNER)}


def save_device_config(config: DeviceConfigFile) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    DEVICE_CONFIG_FILE.write_text(json.dumps(config, indent=2))
    logger.info("Device configuration saved to %s", DEVICE_CONFIG_FILE)


def save_printer_settings(
    name: str, dpi: int = 0, paper_size: str = "A4",
) -> None:
    config = load_device_config()
    config["printer"] = {"name": name, "dpi": dpi, "paper_size": paper_size}
    save_device_config(config)


def save_scanner_settings(
    device: str, dpi: int = 1200, mode: str = "Color",
) -> None:
    config = load_device_config()
    config["scanner"] = {"device": device, "dpi": dpi, "mode": mode}
    save_device_config(config)


def get_printer_settings() -> PrinterSettings:
    return load_device_config()["printer"]


def get_scanner_settings() -> ScannerSettings:
    return load_device_config()["scanner"]
