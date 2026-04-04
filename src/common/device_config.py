import json
import logging
from pathlib import Path
from typing import Any

from common.data_store import DATA_ROOT

logger = logging.getLogger(__name__)

CONFIG_DIR = DATA_ROOT
DEVICE_CONFIG_FILE = CONFIG_DIR / "devices.json"
LEGACY_SCANNER_FILE = CONFIG_DIR / "scanner.json"

EMPTY_PRINTER = {"name": "", "dpi": 0, "paper_size": "A4"}
EMPTY_SCANNER = {"device": "", "dpi": 1200, "mode": "Color"}


def _migrate_legacy() -> dict[str, Any] | None:
    if not LEGACY_SCANNER_FILE.exists():
        return None
    try:
        legacy = json.loads(LEGACY_SCANNER_FILE.read_text())
        return {
            "printer": dict(EMPTY_PRINTER),
            "scanner": {
                "device": legacy.get("device", ""),
                "dpi": legacy.get("dpi", 1200),
                "mode": "Color",
            },
        }
    except (json.JSONDecodeError, KeyError):
        return None


def load_device_config() -> dict[str, Any]:
    if DEVICE_CONFIG_FILE.exists():
        try:
            raw = json.loads(DEVICE_CONFIG_FILE.read_text())
            return {
                "printer": {**EMPTY_PRINTER, **raw.get("printer", {})},
                "scanner": {**EMPTY_SCANNER, **raw.get("scanner", {})},
            }
        except (json.JSONDecodeError, KeyError):
            pass
    migrated = _migrate_legacy()
    if migrated:
        save_device_config(migrated)
        return migrated
    return {"printer": dict(EMPTY_PRINTER), "scanner": dict(EMPTY_SCANNER)}


def save_device_config(config: dict[str, Any]) -> None:
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


def get_printer_settings() -> dict[str, Any]:
    return load_device_config()["printer"]


def get_scanner_settings() -> dict[str, Any]:
    return load_device_config()["scanner"]
