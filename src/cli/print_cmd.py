from pathlib import Path

import typer
from rich.console import Console

from cli.display import print_error, print_success
from common.cups_client import get_printer_capabilities, list_printers, print_file
from common.device_config import get_printer_settings, save_printer_settings

console = Console()


def _resolve_printer(name: str | None) -> str | None:
    if name:
        return name
    saved = get_printer_settings()
    if saved.get("name"):
        return saved["name"]
    printers = list_printers()
    default = next((p for p in printers if p.is_default), None)
    if default:
        return default.name
    if printers:
        return printers[0].name
    return None


def _validate_options(
    printer_name: str,
    resolution: str | None,
    paper_size: str | None,
) -> bool:
    caps = get_printer_capabilities(printer_name)
    if caps is None:
        console.print("[yellow]Could not verify printer capabilities[/yellow]")
        return True
    if resolution and caps.resolutions:
        valid_strs = {f"{x}x{y}dpi" for x, y in caps.resolutions}
        valid_strs |= {f"{x}dpi" for x, y in caps.resolutions if x == y}
        if resolution not in valid_strs:
            print_error(
                f"Resolution {resolution} not supported. "
                f"Available: {', '.join(sorted(valid_strs))}"
            )
            return False
    if paper_size and caps.paper_sizes:
        if paper_size not in caps.paper_sizes:
            print_error(
                f"Paper size {paper_size} not supported. "
                f"Available: {', '.join(caps.paper_sizes[:15])}"
            )
            return False
    return True


def print_command(
    files: list[Path] = typer.Argument(..., help="PNG file(s) to print"),
    printer: str | None = typer.Option(None, help="Printer name (default: saved or system default)"),
    resolution: str | None = typer.Option(None, help="Print resolution (e.g. 600dpi, 1200x1200dpi)"),
    paper_size: str | None = typer.Option(None, "--paper-size", help="Paper size (e.g. A4, Letter)"),
    color_mode: str | None = typer.Option(None, help="Color mode (e.g. RGB, Gray, CMYK)"),
    duplex: str | None = typer.Option(None, help="Duplex mode (e.g. None, DuplexNoTumble)"),
    save_default: bool = typer.Option(False, help="Save printer as default for future jobs"),
) -> None:
    """Print encoded PNG page(s) to a CUPS printer."""
    for f in files:
        if not f.exists():
            print_error(f"File not found: {f}")
            raise typer.Exit(1)

    printer_name = _resolve_printer(printer)
    if not printer_name:
        print_error("No printer available. Run 'paper-clip devices' to check.")
        raise typer.Exit(1)

    if not _validate_options(printer_name, resolution, paper_size):
        raise typer.Exit(1)

    if save_default:
        res_int = 0
        if resolution:
            import re
            match = re.match(r"(\d+)", resolution)
            res_int = int(match.group(1)) if match else 0
        save_printer_settings(
            name=printer_name,
            dpi=res_int,
            paper_size=paper_size or "A4",
        )
        console.print(f"[cyan]Saved {printer_name} as default printer[/cyan]")

    console.print(f"[bold]Printing {len(files)} page(s) to {printer_name}[/bold]")
    if resolution:
        console.print(f"Resolution: {resolution}")
    if paper_size:
        console.print(f"Paper size: {paper_size}")
    console.print()

    for f in files:
        job_id = print_file(
            printer_name, f,
            title=f"paper-clip: {f.name}",
            resolution=resolution,
            paper_size=paper_size,
            color_mode=color_mode,
            duplex=duplex,
        )
        if job_id is not None:
            print_success(f"Submitted {f.name} (job {job_id})")
        else:
            print_error(f"Failed to print {f.name}")
