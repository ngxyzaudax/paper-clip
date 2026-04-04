from pathlib import Path

import typer
from rich.console import Console
from rich.prompt import Confirm

from cli.display import print_error, print_success
from common.capture import run_capture_session
from common.config import ALGO_FIELDS
from common.config_store import load_profile
from common.cups_client import list_printers
from common.data_store import create_job, digital_dir, find_job, update_job_metadata
from common.device_config import get_scanner_settings
from common.page_layout import data_capacity_bytes
from serialization.encode.pipeline import encode

console = Console()


def _resolve_printer(printer: str | None) -> str:
    if printer:
        return printer
    printers = list_printers()
    default = [p for p in printers if p.is_default]
    if not default:
        print_error("No default printer found. Specify --printer")
        raise typer.Exit(1)
    return default[0].name


def _resolve_scanner() -> tuple[str, int, str]:
    scanner = get_scanner_settings()
    device = scanner.get("device", "")
    if not device:
        print_error("No scanner configured. Run: paper-clip scan --save-config --device '<dev>'")
        raise typer.Exit(1)
    return device, scanner.get("dpi", 1200), scanner.get("mode", "Color")


def _encode_job(
    input_path: Path, profile: str, password: str | None,
) -> tuple[Path, list[Path], int]:
    config = load_profile(profile)
    from common.config import FLAG_ENCRYPTED
    flags = FLAG_ENCRYPTED if password else 0
    file_size = input_path.stat().st_size
    total_pages = max(1, -(-file_size // data_capacity_bytes(config)))
    config_dict = {k: getattr(config, k) for k in ALGO_FIELDS}
    job_dir = create_job(input_path.name, profile, config_dict, total_pages)
    output_base = digital_dir(job_dir) / "page"
    png_paths = encode(input_path, output_base, config, flags=flags, passphrase=password)
    return job_dir, png_paths, config.scan_dpi


def _generate_and_encode(
    profile: str, pages: int, password: str | None,
) -> tuple[Path, list[Path], int]:
    from common.test_data import generate_test_payload, save_test_file
    config = load_profile(profile)
    from common.config import FLAG_ENCRYPTED
    flags = FLAG_ENCRYPTED if password else 0
    data = generate_test_payload(config, pages)
    config_dict = {k: getattr(config, k) for k in ALGO_FIELDS}
    job_dir = create_job(f"testdata_{pages}p", profile, config_dict, pages)
    test_path, sha256 = save_test_file(data, job_dir)
    console.print(f"[cyan]Test data:  {test_path.name} ({len(data):,} bytes)[/cyan]")
    console.print(f"[cyan]SHA-256:    {sha256}[/cyan]")
    update_job_metadata(job_dir, {
        "test_data": True, "original_sha256": sha256, "original_size": len(data),
    })
    output_base = digital_dir(job_dir) / "page"
    png_paths = encode(test_path, output_base, config, flags=flags, passphrase=password)
    return job_dir, png_paths, config.scan_dpi


def capture_command(
    input_file: Path = typer.Argument(None, help="File to encode (omit with --generate)"),
    profile: str = typer.Option(..., help="Config profile name (see paper-clip config)"),
    scans: int = typer.Option(3, help="Number of scans per page"),
    printer: str | None = typer.Option(None, help="Printer name (default: system default)"),
    password: str | None = typer.Option(None, help="Encrypt with this password"),
    job_id: str | None = typer.Option(None, help="Resume scanning into existing job"),
    generate: bool = typer.Option(False, help="Generate random test data instead of using a file"),
    generate_pages: int = typer.Option(1, help="Pages of random data to generate (with --generate)"),
) -> None:
    """Guided print+scan capture: encode, print each page, prompt to scan."""
    scanner_device, scanner_dpi, scanner_mode = _resolve_scanner()
    printer_name = _resolve_printer(printer)
    console.print(f"[cyan]Printer: {printer_name}[/cyan]")
    console.print(f"[cyan]Scanner: {scanner_device} @ {scanner_dpi} DPI[/cyan]\n")

    if job_id:
        jd = find_job(job_id)
        if not jd:
            print_error(f"No job found matching: {job_id}")
            raise typer.Exit(1)
        from common.data_store import load_job_metadata
        render_dpi = load_job_metadata(jd).get("config", {}).get("scan_dpi", 1200)
        digital_pages = sorted((jd / "digital").glob("*.png"))
        job_dir = jd
        console.print(f"[cyan]Resuming job: {jd.name} ({len(digital_pages)} pages)[/cyan]")
    elif generate:
        console.print(f"[bold]Generating {generate_pages} page(s) of random test data...[/bold]")
        job_dir, digital_pages, render_dpi = _generate_and_encode(profile, generate_pages, password)
        for p in digital_pages:
            print_success(f"Rendered: {p.name}")
        console.print()
    else:
        if input_file is None or not input_file.exists():
            print_error("Provide an input file or use --generate")
            raise typer.Exit(1)
        console.print(f"[bold]Encoding {input_file.name}...[/bold]")
        job_dir, digital_pages, render_dpi = _encode_job(input_file, profile, password)
        for p in digital_pages:
            print_success(f"Rendered: {p.name}")
        console.print()

    print_res = f"{render_dpi}dpi"
    console.print(f"[cyan]Print: {print_res} | Scan: {scanner_dpi} DPI[/cyan]\n")

    def on_status(msg: str) -> None:
        console.print(f"  {msg}")

    def on_prompt(msg: str) -> bool:
        return Confirm.ask(f"\n[bold yellow]{msg}[/bold yellow]", console=console)

    console.print(f"[bold]Capture: {len(digital_pages)} page(s), {scans} scan(s) each[/bold]\n")
    masters = run_capture_session(
        job_dir, digital_pages, printer_name,
        scanner_device, scanner_dpi, scanner_mode, scans,
        print_resolution=print_res,
        on_status=on_status, on_prompt=on_prompt,
    )

    console.print(f"\n[bold green]Capture complete: {len(masters)} master(s)[/bold green]")
    console.print(f"[bold]Job: {job_dir}[/bold]")
    for m in masters:
        console.print(f"  [green]{m}[/green]")
