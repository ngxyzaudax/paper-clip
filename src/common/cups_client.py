import logging
from pathlib import Path

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


def print_files(
    printer_name: str,
    files: list[Path],
    job_title: str,
    options: dict[str, str] | None = None,
) -> list[int]:
    conn = _get_connection()
    if conn is None:
        raise RuntimeError("Printer connection unavailable")
    if not printer_name:
        raise ValueError("printer_name is required")
    printers = conn.getPrinters()
    if printer_name not in printers:
        raise RuntimeError(f"Printer not found: {printer_name}")
    if not files:
        raise ValueError("No files to print")
    opts = options or {}
    job_ids: list[int] = []
    total = len(files)
    for idx, file_path in enumerate(files, start=1):
        if not file_path.exists():
            raise FileNotFoundError(str(file_path))
        title = f"{job_title} ({idx}/{total})" if total > 1 else job_title
        job_id = conn.printFile(printer_name, str(file_path), title, opts)
        job_ids.append(int(job_id))
    return job_ids
