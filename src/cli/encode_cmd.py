from pathlib import Path

import typer
from rich.console import Console

from cli.display import make_page_callback, make_page_progress, print_error, print_success
from cli.encode_plan import show_encoding_plan
from cli.encoding_cli import cli_encoding_config
from common.config import ALGO_FIELDS
from common.data_store import create_print_job, digital_dir
from common.page_layout import data_capacity_bytes, pages_needed
from common.paper_sizes import detect_paper_size
from serialization.encode.pipeline import encode

console = Console()


def encode_command(
    input_file: Path = typer.Argument(..., help="File to encode"),
    num_symbols: int | None = typer.Option(
        None,
        "--num-symbols",
        help=(
            "Per-cell alphabet: 5=CMYK+blank, 8=+R/G/B overprints+blank, 11=+K-tints+blank; "
            "0 is always blank. Allowed values: 5, 8, 11."
        ),
    ),
    cell_size_px: int | None = typer.Option(
        None,
        help="Cell size in pixels (default 32). Presets: 24, 32, 40, 48, 64. Must be at least 0.6 mm.",
    ),
    paper_size: str | None = typer.Option(None, help="Paper size (A3, A4, A5, Letter, Legal, etc.)"),
    print_dpi: int | None = typer.Option(None, help="Logical page DPI for layout and print hints"),
    rs_redundancy: float | None = typer.Option(None, help="Reed–Solomon redundancy (0.05–0.50)"),
    redundancy_pages: int | None = typer.Option(None, help="Extra parity pages (fountain)"),
    margin_mm: float | None = typer.Option(None, help="Uniform page margin in mm (all sides)"),
    margin_top_mm: float | None = typer.Option(None, help="Top page margin in mm"),
    margin_right_mm: float | None = typer.Option(None, help="Right page margin in mm"),
    margin_bottom_mm: float | None = typer.Option(None, help="Bottom page margin in mm"),
    margin_left_mm: float | None = typer.Option(None, help="Left page margin in mm"),
    password: str | None = typer.Option(
        None,
        help="Passphrase for payload encryption (built-in default key when omitted)",
    ),
) -> None:
    """Encode a file into print-ready PNG page(s). Saves into data/print/jobs/ by default."""
    if not input_file.exists():
        print_error(f"File not found: {input_file}")
        raise typer.Exit(1)

    config = cli_encoding_config(
        num_symbols, cell_size_px, paper_size,
        print_dpi, rs_redundancy, redundancy_pages, margin_mm,
        margin_top_mm, margin_right_mm, margin_bottom_mm, margin_left_mm,
    )

    from serialization.encode.encoder import prepare_payload

    raw_data = input_file.read_bytes()
    file_size = len(raw_data)
    prepared = prepare_payload(
        raw_data, config, filename=input_file.name, passphrase=password,
    )
    payload = prepared.payload
    data_pages = pages_needed(len(payload), config)
    total_pages = data_pages + config.redundancy_pages
    config_dict = {k: getattr(config, k) for k in ALGO_FIELDS}
    for k in (
        "margin_top_mm",
        "margin_right_mm",
        "margin_bottom_mm",
        "margin_left_mm",
        "page_width_mm",
        "page_height_mm",
    ):
        config_dict[k] = getattr(config, k)
    job_dir = create_print_job(
        input_file.name, "inline", config_dict, total_pages,
        paper_size=detect_paper_size(config.page_width_mm, config.page_height_mm),
        data_pages=data_pages,
        payload_bytes=len(payload),
        data_capacity_bytes_per_page=data_capacity_bytes(config),
    )
    output_base = digital_dir(job_dir) / "page"
    console.print(f"[cyan]Job created: {job_dir}[/cyan]\n")

    show_encoding_plan(input_file, output_base.parent, config, file_size, len(payload))
    if password:
        console.print("[bold yellow]User passphrase in use[/bold yellow]")
    console.print()

    progress, task = make_page_progress("Rendering pages")
    with progress:
        png_paths = encode(
            input_file, output_base, config,
            on_page_complete=make_page_callback(progress, task),
            passphrase=password,
            prepared=prepared,
        )

    for p in png_paths:
        print_success(f"Saved {p}")
    console.print(f"\n[bold]Job directory: {job_dir}[/bold]")
