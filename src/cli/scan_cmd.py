from pathlib import Path

import typer
from rich.console import Console

from cli.display import print_error, print_success
from common.data_store import find_job, scans_page_dir
from common.device_config import get_scanner_settings, save_scanner_settings
from common.sane_client import scan_page
from common.scan_session import save_master, session_dir

console = Console()


def _save_scan(image: "Image.Image", output_file: Path) -> None:
    image.save(str(output_file), format="PNG")


def scan_command(
    count: int = typer.Option(1, help="Number of scans to perform"),
    page: int = typer.Option(1, help="Page number being scanned (1-based)"),
    job: str | None = typer.Option(None, help="Job ID prefix to save scans into"),
    output_dir: Path = typer.Option("./scans", help="Base directory (used when no job specified)"),
    device: str | None = typer.Option(None, help="Scanner device string"),
    dpi: int | None = typer.Option(None, help="Scan resolution in DPI"),
    mode: str | None = typer.Option(None, help="Scan mode (e.g. Color, Gray)"),
    save_config: bool = typer.Option(False, help="Save device/dpi/mode as default scanner config"),
) -> None:
    """Scan pages into a job or a timestamped subfolder. Produces a master averaged image."""
    scanner = get_scanner_settings()
    actual_device = device or scanner.get("device", "")
    actual_dpi = dpi or scanner.get("dpi", 1200)
    actual_mode = mode or scanner.get("mode", "Color")

    if save_config:
        save_scanner_settings(actual_device, actual_dpi, actual_mode)
        console.print("[cyan]Scanner config saved[/cyan]")

    if job:
        job_dir = find_job(job)
        if not job_dir:
            print_error(f"No job found matching: {job}")
            raise typer.Exit(1)
        run_dir = scans_page_dir(job_dir, page - 1)
        console.print(f"[cyan]Scanning into job: {job_dir.name}, page {page}[/cyan]")
    else:
        run_dir = session_dir(output_dir.expanduser())
        run_dir.mkdir(parents=True, exist_ok=True)

    console.print(f"[bold]Scanning {count} image(s) at {actual_dpi} DPI[/bold]")
    console.print(f"Device:  {actual_device}")
    console.print(f"Session: {run_dir}\n")

    scanned: list[Path] = []
    for i in range(count):
        outfile = run_dir / f"scan_{i + 1:03d}.png"
        console.print(f"  Scanning to {outfile.name}...")
        image = scan_page(actual_device, actual_dpi, actual_mode)
        if image is not None:
            _save_scan(image, outfile)
            scanned.append(outfile)
            print_success(f"Scan {i + 1}/{count} saved: {outfile.name}")
        else:
            print_error(f"Scan {i + 1}/{count} failed")

    if not scanned:
        print_error("No scans succeeded.")
        return

    master = save_master(scanned, run_dir)
    console.print(f"\n[bold]{len(scanned)}/{count} scans completed[/bold]")
    console.print(f"[green]Master: {master}[/green]")
