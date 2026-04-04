import typer
from rich.console import Console
from rich.table import Table

from common.cups_client import get_printer_capabilities, list_printers
from common.sane_client import get_scanner_capabilities, list_scanners

console = Console()


def _show_printers() -> None:
    printers = list_printers()
    if not printers:
        console.print("[yellow]No printers found (is CUPS running?)[/yellow]")
        console.print("[dim]Install libcups2-dev and pycups for printer discovery[/dim]")
        return
    table = Table(title="Available Printers", show_header=True, header_style="bold cyan")
    table.add_column("Name", style="bold")
    table.add_column("State")
    table.add_column("URI", style="dim")
    table.add_column("Default")
    for p in printers:
        table.add_row(p.name, p.state, p.uri, "yes" if p.is_default else "")
    console.print(table)

    for p in printers:
        caps = get_printer_capabilities(p.name)
        if caps is None:
            continue
        detail = Table(
            title=f"Capabilities: {p.name}",
            show_header=True, header_style="bold green",
        )
        detail.add_column("Property", style="bold")
        detail.add_column("Values")
        detail.add_row(
            "Resolutions",
            ", ".join(f"{x}x{y}" for x, y in caps.resolutions) or "not reported",
        )
        detail.add_row("Paper sizes", ", ".join(caps.paper_sizes[:15]) or "none")
        detail.add_row("Color modes", ", ".join(caps.color_modes) or "none")
        detail.add_row("Duplex", ", ".join(caps.duplex_modes) or "none")
        console.print(detail)


def _show_scanners() -> None:
    scanners = list_scanners()
    if not scanners:
        console.print("[yellow]No scanners found[/yellow]")
        console.print("[dim]Install libsane-dev and python-sane for scanner discovery[/dim]")
        return
    table = Table(title="Available Scanners", show_header=True, header_style="bold cyan")
    table.add_column("Device ID", style="bold")
    table.add_column("Vendor")
    table.add_column("Model")
    table.add_column("Type")
    for s in scanners:
        table.add_row(s.device_id, s.vendor, s.model, s.device_type)
    console.print(table)

    for s in scanners:
        caps = get_scanner_capabilities(s.device_id)
        if caps is None:
            continue
        detail = Table(
            title=f"Capabilities: {s.model}",
            show_header=True, header_style="bold green",
        )
        detail.add_column("Property", style="bold")
        detail.add_column("Values")
        detail.add_row(
            "Resolutions (DPI)",
            ", ".join(str(r) for r in caps.resolutions) or "not reported",
        )
        detail.add_row("Modes", ", ".join(caps.modes) or "none")
        detail.add_row("Sources", ", ".join(caps.sources) or "none")
        console.print(detail)


def devices_command(
    printers_only: bool = typer.Option(False, "--printers", help="Show printers only"),
    scanners_only: bool = typer.Option(False, "--scanners", help="Show scanners only"),
) -> None:
    """Discover available printers and scanners with their capabilities."""
    if not scanners_only:
        _show_printers()
        console.print()
    if not printers_only:
        _show_scanners()
