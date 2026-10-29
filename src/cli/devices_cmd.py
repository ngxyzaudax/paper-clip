import typer
from rich.console import Console
from rich.table import Table

from common.device_discover import list_escl_scanners, list_ipp_printers
from common.device_error import DeviceError
from common.escl_scan import scanner_capabilities
from common.ipp_client import printer_attributes
from common.ipp_options import build_ticket
from common.sane_discovery import list_scanners

console = Console()


def devices_command(
    printers_only: bool = typer.Option(False, "--printers", help="Show printers only"),
    scanners_only: bool = typer.Option(False, "--scanners", help="Show scanners only"),
) -> None:
    """Discover IPP Everywhere printers and eSCL scanners."""
    if not scanners_only:
        _show_printers()
        console.print()
    if not printers_only:
        _show_scanners()


def _show_printers() -> None:
    printers = list_ipp_printers()
    if not printers:
        console.print("[yellow]No IPP printers found.[/yellow]")
        console.print("[dim]Set printer.uri in data/devices.json or check that the printer is on the network.[/dim]")
        return
    table = Table(title="IPP printers", show_header=True, header_style="bold cyan")
    table.add_column("Name", style="bold")
    table.add_column("State")
    table.add_column("URI")
    for printer in printers:
        table.add_row(printer.name, printer.state, printer.uri)
    console.print(table)
    for printer in printers:
        console.print(_printer_detail(printer.uri))


def _show_scanners() -> None:
    scanners = list_escl_scanners()
    sane = list_scanners()
    if not scanners and not sane:
        console.print("[yellow]No eSCL scanners found.[/yellow]")
        console.print("[dim]Set scanner.uri in data/devices.json or check that the scanner is on the network.[/dim]")
        return
    table = Table(title="eSCL scanners", show_header=True, header_style="bold cyan")
    table.add_column("Model", style="bold")
    table.add_column("URI")
    for scanner in scanners:
        table.add_row(scanner.model or scanner.device_id, scanner.device_id)
    for scanner in sane:
        table.add_row(scanner.model or scanner.device_id, scanner.device_id + " (sane)")
    console.print(table)
    for scanner in scanners:
        console.print(_scanner_detail(scanner.device_id))


def _printer_detail(uri: str) -> str:
    try:
        ticket = build_ticket(printer_attributes(uri), "A4")
    except DeviceError as exc:
        return f"[yellow]{uri}: {exc}[/yellow]"
    return (
        f"[green]{uri}[/green]\n"
        f"  {ticket.document_format} at {ticket.dpi} dpi, {ticket.media.keyword}\n"
        f"  source {ticket.source}, margin {ticket.margin / 100:.1f} mm, "
        f"{ticket.color}, quality {ticket.quality}, scaling {ticket.scaling}, {ticket.sides}"
    )


def _scanner_detail(uri: str) -> str:
    try:
        caps = scanner_capabilities(uri)
    except DeviceError as exc:
        return f"[yellow]{uri}: {exc}[/yellow]"
    resolutions = ", ".join(str(item) for item in caps.resolutions) or "not reported"
    return f"[green]{uri}[/green]\n  {caps.model} {caps.source} dpi {resolutions} formats {', '.join(caps.formats) or 'jpeg'}"
