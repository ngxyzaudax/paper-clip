from common.device_config import get_printer_settings, get_scanner_settings
from common.types import PrinterInfo, ScannerInfo


def printer_section_placeholder(
    options: list[tuple[str, str]],
    selected: str | None,
) -> str | None:
    if not options:
        return "[yellow]No printers found.[/yellow]"
    if not selected:
        return (
            "[dim]Choose a printer on the left to see resolutions, paper sizes, "
            "color modes, and duplex options.[/dim]"
        )
    return None


def scanner_section_placeholder(
    options: list[tuple[str, str]],
    selected: str | None,
) -> str | None:
    if not options:
        return "[yellow]No scanners found.[/yellow]"
    if not selected:
        return (
            "[dim]Choose a scanner on the left to see DPI, modes, and sources.[/dim]"
        )
    return None


def pick_button_label(
    options: list[tuple[str, str]],
    value: str | None,
    *,
    absent_message: str,
) -> str:
    if not options:
        return absent_message
    if not value:
        return "[dim]Select…[/dim]"
    for lab, v in options:
        if v == value:
            return lab
    return value


def discover_printers(
    printers_out: list[PrinterInfo],
) -> tuple[list[tuple[str, str]], str | None]:
    from common.device_discover import list_ipp_printers

    printers_out.clear()
    printers_out.extend(list_ipp_printers())
    saved = str(get_printer_settings().get("uri", ""))
    options = [
        (f"{printer.name} ({printer.state})", printer.uri)
        for printer in printers_out
    ]
    initial = saved if any(printer.uri == saved for printer in printers_out) else None
    if initial is None and printers_out:
        initial = printers_out[0].uri
    return options, initial


def discover_scanners(
    scanners_out: list[ScannerInfo],
) -> tuple[list[tuple[str, str]], str | None]:
    from common.device_discover import list_escl_scanners, saved_scanner_uri
    from common.sane_discovery import list_scanners

    scanners_out.clear()
    scanners_out.extend(list_escl_scanners())
    scanners_out.extend(list_scanners())
    saved = saved_scanner_uri() or str(get_scanner_settings().get("device", ""))
    options = [
        (f"{scanner.vendor} {scanner.model}".strip() or scanner.device_id, scanner.device_id)
        for scanner in scanners_out
    ]
    initial = saved if any(scanner.device_id == saved for scanner in scanners_out) else None
    if initial is None and scanners_out:
        initial = scanners_out[0].device_id
    return options, initial


def format_printer_caps(printer_uri: str) -> str:
    from common.device_error import DeviceError
    from common.ipp_client import printer_attributes
    from common.ipp_options import build_ticket

    paper = str(get_printer_settings().get("paper_size") or "A4")
    try:
        ticket = build_ticket(printer_attributes(printer_uri), paper)
    except DeviceError as exc:
        return f"[yellow]{exc}[/yellow]"
    return (
        f"[bold]URI:[/bold] {printer_uri}\n"
        f"[bold]Document:[/bold] {ticket.document_format} at {ticket.dpi} dpi\n"
        f"[bold]Media:[/bold] {ticket.media.keyword}, {ticket.source}, "
        f"{ticket.margin / 100:.1f} mm margin\n"
        f"[bold]Print:[/bold] {ticket.color}, quality {ticket.quality}, "
        f"scaling {ticket.scaling}, {ticket.sides}"
    )


def format_scanner_caps(device_id: str) -> str:
    if device_id.startswith(("http://", "https://")):
        return _escl_caps(device_id)
    from common.sane_discovery import get_scanner_capabilities

    caps = get_scanner_capabilities(device_id)
    if caps is None:
        return "[yellow]Could not read capabilities[/yellow]"
    resolutions = ", ".join(str(item) for item in caps.resolutions) or "not reported"
    return (
        f"[bold]DPI:[/bold] {resolutions}\n"
        f"[bold]Modes:[/bold] {', '.join(caps.modes) or 'none'}\n"
        f"[bold]Sources:[/bold] {', '.join(caps.sources) or 'none'}"
    )


def _escl_caps(uri: str) -> str:
    from common.device_error import DeviceError
    from common.escl_scan import scanner_capabilities

    try:
        caps = scanner_capabilities(uri)
    except DeviceError as exc:
        return f"[yellow]{exc}[/yellow]"
    resolutions = ", ".join(str(item) for item in caps.resolutions) or "not reported"
    return (
        f"[bold]URI:[/bold] {uri}\n"
        f"[bold]DPI:[/bold] {resolutions}\n"
        f"[bold]Modes:[/bold] {', '.join(caps.color_modes) or 'RGB24'}\n"
        f"[bold]Source:[/bold] {caps.source}"
    )
