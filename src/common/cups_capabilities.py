import logging
import os
import re

from common.types import PrinterCapabilities

logger = logging.getLogger(__name__)


def _parse_resolution(choice_str: str) -> tuple[int, int] | None:
    match = re.match(r"(\d+)x(\d+)dpi", choice_str)
    if match:
        return int(match.group(1)), int(match.group(2))
    match = re.match(r"(\d+)dpi", choice_str)
    if match:
        val = int(match.group(1))
        return val, val
    return None


def _extract_ppd_options(ppd: "cups.PPD") -> dict[str, list[dict[str, str]]]:
    options: dict[str, list[dict[str, str]]] = {}
    for group in ppd.optionGroups:
        for opt in group.options:
            options[opt.keyword] = [
                {"choice": c["choice"], "text": c["text"]}
                for c in opt.choices
            ]
    return options


def _resolutions_from_options(
    options: dict[str, list[dict[str, str]]],
) -> list[tuple[int, int]]:
    result: list[tuple[int, int]] = []
    for choice in options.get("Resolution", []):
        parsed = _parse_resolution(choice["choice"])
        if parsed:
            result.append(parsed)
    return sorted(result)


def get_printer_capabilities(
    conn: "cups.Connection", printer_name: str,
) -> PrinterCapabilities | None:
    ppd_path = None
    try:
        import cups
        ppd_path = conn.getPPD(printer_name)
        ppd = cups.PPD(ppd_path)
        ppd.markDefaults()
        options = _extract_ppd_options(ppd)
    except Exception as exc:
        logger.warning("Failed to read PPD for %s: %s", printer_name, exc)
        return _capabilities_from_ipp(conn, printer_name)
    finally:
        if ppd_path:
            try:
                os.unlink(ppd_path)
            except OSError:
                pass

    resolutions = _resolutions_from_options(options)
    paper_sizes = [c["choice"] for c in options.get("PageSize", [])]
    color_modes = [c["choice"] for c in options.get("ColorModel", [])]
    duplex_modes = [c["choice"] for c in options.get("Duplex", [])]
    return PrinterCapabilities(
        resolutions=resolutions,
        paper_sizes=paper_sizes,
        color_modes=color_modes,
        duplex_modes=duplex_modes,
    )


def _capabilities_from_ipp(
    conn: "cups.Connection", printer_name: str,
) -> PrinterCapabilities | None:
    try:
        attrs = conn.getPrinterAttributes(printer_name)
    except Exception as exc:
        logger.warning("IPP attribute query failed for %s: %s", printer_name, exc)
        return None

    raw_res = attrs.get("printer-resolution-supported", [])
    if isinstance(raw_res, str):
        raw_res = [raw_res]
    resolutions: list[tuple[int, int]] = []
    for r in raw_res:
        parsed = _parse_resolution(str(r))
        if parsed:
            resolutions.append(parsed)

    raw_media = attrs.get("media-supported", [])
    if isinstance(raw_media, str):
        raw_media = [raw_media]

    raw_sides = attrs.get("sides-supported", [])
    if isinstance(raw_sides, str):
        raw_sides = [raw_sides]

    color = attrs.get("color-supported", False)
    color_modes = ["Color", "Gray"] if color else ["Gray"]

    return PrinterCapabilities(
        resolutions=sorted(resolutions),
        paper_sizes=list(raw_media),
        color_modes=color_modes,
        duplex_modes=list(raw_sides),
    )
