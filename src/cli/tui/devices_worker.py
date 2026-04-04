from common.device_config import get_printer_settings, get_scanner_settings
from common.types import PrinterInfo, ScannerInfo
from textual.widgets import Select


def discover_printers(
    printers_out: list[PrinterInfo],
) -> tuple[list[tuple[str, str]], "str | type"]:
    from common.cups_client import list_printers
    printers_out.clear()
    printers_out.extend(list_printers())
    saved = get_printer_settings()
    options = [
        (f"{p.name} ({p.state})" + (" [default]" if p.is_default else ""), p.name)
        for p in printers_out
    ]
    saved_name = saved.get("name", "")
    initial = saved_name if any(p.name == saved_name for p in printers_out) else Select.BLANK
    return options, initial


def discover_scanners(
    scanners_out: list[ScannerInfo],
) -> tuple[list[tuple[str, str]], "str | type"]:
    from common.sane_client import list_scanners
    scanners_out.clear()
    scanners_out.extend(list_scanners())
    saved = get_scanner_settings()
    options = [
        (f"{s.vendor} {s.model}" if s.vendor else s.device_id, s.device_id)
        for s in scanners_out
    ]
    saved_device = saved.get("device", "")
    initial = saved_device if any(s.device_id == saved_device for s in scanners_out) else Select.BLANK
    return options, initial


def format_printer_caps(printer_name: str) -> str:
    from common.cups_client import get_printer_capabilities
    caps = get_printer_capabilities(printer_name)
    if caps is None:
        return "[yellow]Could not read capabilities[/yellow]"
    res_str = ", ".join(f"{x}x{y}" for x, y in caps.resolutions) or "not reported"
    paper_str = ", ".join(caps.paper_sizes[:10]) or "none"
    color_str = ", ".join(caps.color_modes) or "none"
    duplex_str = ", ".join(caps.duplex_modes) or "none"
    return (
        f"[bold]Resolutions:[/bold] {res_str}\n"
        f"[bold]Paper:[/bold] {paper_str}\n"
        f"[bold]Color:[/bold] {color_str}\n"
        f"[bold]Duplex:[/bold] {duplex_str}"
    )


def format_scanner_caps(device_id: str) -> str:
    from common.sane_client import get_scanner_capabilities
    caps = get_scanner_capabilities(device_id)
    if caps is None:
        return "[yellow]Could not read capabilities[/yellow]"
    res_str = ", ".join(str(r) for r in caps.resolutions) or "not reported"
    mode_str = ", ".join(caps.modes) or "none"
    source_str = ", ".join(caps.sources) or "none"
    return (
        f"[bold]DPI:[/bold] {res_str}\n"
        f"[bold]Modes:[/bold] {mode_str}\n"
        f"[bold]Sources:[/bold] {source_str}"
    )
