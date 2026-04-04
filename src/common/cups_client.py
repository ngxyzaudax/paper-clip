import logging

from common.types import PrinterCapabilities, PrinterInfo

logger = logging.getLogger(__name__)

CUPS_STATE_MAP = {3: "idle", 4: "printing", 5: "stopped"}


def _get_connection() -> "cups.Connection | None":
    try:
        import cups
        return cups.Connection()
    except ImportError:
        logger.warning("pycups not installed; printer discovery unavailable")
        return None
    except RuntimeError as exc:
        logger.warning("CUPS connection failed: %s", exc)
        return None


def list_printers() -> list[PrinterInfo]:
    conn = _get_connection()
    if conn is None:
        return []
    try:
        raw = conn.getPrinters()
        default_name = conn.getDefault() or ""
    except Exception as exc:
        logger.warning("Failed to enumerate printers: %s", exc)
        return []
    return [
        PrinterInfo(
            name=name,
            uri=info.get("device-uri", ""),
            state=CUPS_STATE_MAP.get(info.get("printer-state", 0), "unknown"),
            is_default=(name == default_name),
        )
        for name, info in raw.items()
    ]


def get_printer_capabilities(printer_name: str) -> PrinterCapabilities | None:
    conn = _get_connection()
    if conn is None:
        return None
    from common.cups_capabilities import get_printer_capabilities as _get_caps
    return _get_caps(conn, printer_name)
