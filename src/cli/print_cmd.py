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
) -> str | None:
    caps = get_printer_capabilities(printer_name)
    if caps is None:
        return None
    if resolution and caps.resolutions:
        valid_strs = {f"{x}x{y}dpi" for x, y in caps.resolutions}
        valid_strs |= {f"{x}dpi" for x, y in caps.resolutions if x == y}
        if resolution not in valid_strs:
            return (
                f"Resolution {resolution} not supported. "
                f"Available: {', '.join(sorted(valid_strs))}"
            )
    if paper_size and caps.paper_sizes:
        if paper_size not in caps.paper_sizes:
            return (
                f"Paper size {paper_size} not supported. "
                f"Available: {', '.join(caps.paper_sizes[:15])}"
            )
    return None


def run_print_job(
    files: list[Path],
    printer: str | None,
    resolution: str | None,
    paper_size: str | None,
    color_mode: str | None,
    duplex: str | None,
    save_default: bool,
) -> tuple[str, str, list[tuple[str, int]]]:
    for f in files:
        if not f.exists():
            return f"File not found: {f}", "", []

    printer_name = _resolve_printer(printer)
    if not printer_name:
        return "No printer available. Run 'paper-clip devices' to check.", "", []

    opt_err = _validate_options(printer_name, resolution, paper_size)
    if opt_err:
        return opt_err, "", []

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

    results: list[tuple[str, int]] = []
    for f in files:
        job_id = print_file(
            printer_name, f,
            title=f"paper-clip: {f.name}",
            resolution=resolution,
            paper_size=paper_size,
            color_mode=color_mode,
            duplex=duplex,
        )
        if job_id is None:
            return f"Failed to print {f.name}", printer_name, []
        results.append((f.name, job_id))
    return "", printer_name, results


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
    pre = _resolve_printer(printer)
    if pre and get_printer_capabilities(pre) is None:
        console.print("[yellow]Could not verify printer capabilities[/yellow]")

    err, printer_name, results = run_print_job(
        files, printer, resolution, paper_size, color_mode, duplex, save_default,
    )
    if err:
        print_error(err)
        raise typer.Exit(1)

    if save_default:
        console.print(f"[cyan]Saved {printer_name} as default printer[/cyan]")

    console.print(f"[bold]Printing {len(files)} page(s) to {printer_name}[/bold]")
    if resolution:
        console.print(f"Resolution: {resolution}")
    if paper_size:
        console.print(f"Paper size: {paper_size}")
    console.print()

    for name, job_id in results:
        print_success(f"Submitted {name} (job {job_id})")
