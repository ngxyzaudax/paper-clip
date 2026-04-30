from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from cli.display import (
    config_table,
    file_size_display,
    make_page_callback,
    make_page_progress,
    print_error,
    print_success,
)
from cli.encoding_cli import cli_encoding_config
from common.config import ALGO_FIELDS, PaperClipConfig
from common.data_store import create_job, digital_dir
from common.page_layout import data_capacity_bytes, grid_dimensions, page_image_size, pages_needed
from common.palette import palette_from_config
from common.paper_sizes import detect_paper_size
from common.symbols import bits_per_cell
from serialization.encode.pipeline import encode

console = Console()


def _show_encoding_plan(
    input_path: Path,
    output_dir: Path,
    config: PaperClipConfig,
    source_file_size: int,
    payload_size: int,
) -> None:
    capacity = data_capacity_bytes(config)
    cols, rows = grid_dimensions(config)
    pw, ph = page_image_size(config)
    bpc = bits_per_cell(config.num_symbols)
    sc = config.num_symbols
    data_pages = pages_needed(payload_size, config)
    pages = data_pages + config.redundancy_pages
    palette = palette_from_config(config)
    paper_name = detect_paper_size(config.page_width_mm, config.page_height_mm)
    config_table([
        ("Paper", f"{paper_name} ({config.page_width_mm}x{config.page_height_mm}mm)"),
        ("Symbols", f"{sc} (0…{sc - 1})"),
        ("Cell size", f"{config.cell_size_px} px"),
        ("Bits/cell", f"{bpc:.2f}"),
        ("Grid", f"{cols} x {rows} cells"),
        ("Page image", f"{pw} x {ph} px"),
        ("RS redundancy", f"{config.rs_redundancy:.0%}"),
    ], title="Encoding Configuration")
    console.print("\n[bold]Symbol palette:[/bold]")
    r0, g0, b0 = 255, 255, 255
    block0 = f"[on rgb({r0},{g0},{b0})]      [/on rgb({r0},{g0},{b0})]"
    console.print(f"  0: {block0}  RGB({r0}, {g0}, {b0})  (blank paper, no dot)")
    for sym, (r, g, b) in enumerate(palette, start=1):
        block = f"[on rgb({r},{g},{b})]      [/on rgb({r},{g},{b})]"
        console.print(f"  {sym}: {block}  RGB({r}, {g}, {b})")
    summary = Table(title="\nEncoding Plan", show_header=True, header_style="bold cyan")
    summary.add_column("Detail", style="bold")
    summary.add_column("Value", style="white")
    summary.add_row("Input file", str(input_path))
    summary.add_row("File size", file_size_display(source_file_size))
    summary.add_row("Payload size", file_size_display(payload_size))
    summary.add_row("Capacity/page", file_size_display(capacity))
    summary.add_row("Data pages", str(data_pages))
    summary.add_row("Total pages", str(pages))
    utilization = min(
        100.0,
        (payload_size / (capacity * data_pages)) * 100 if data_pages > 0 else 0.0,
    )
    summary.add_row("Space utilization", f"{utilization:.1f}%")
    summary.add_row("Output", str(output_dir))
    console.print(summary)


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
        None, help="Cell size in pixels. Allowed values: 10, 15, 20, 25.",
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
    """Encode a file into print-ready PNG page(s). Saves into data/jobs/ by default."""
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
    payload, sha256_hash = prepare_payload(
        raw_data, config, filename=input_file.name, passphrase=password,
    )
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
    job_dir = create_job(
        input_file.name, "inline", config_dict, total_pages,
        paper_size=detect_paper_size(config.page_width_mm, config.page_height_mm),
        data_pages=data_pages,
        payload_bytes=len(payload),
        data_capacity_bytes_per_page=data_capacity_bytes(config),
    )
    output_base = digital_dir(job_dir) / "page"
    console.print(f"[cyan]Job created: {job_dir}[/cyan]\n")

    _show_encoding_plan(input_file, output_base.parent, config, file_size, len(payload))
    if password:
        console.print("[bold yellow]User passphrase in use[/bold yellow]")
    console.print()

    progress, task = make_page_progress("Rendering pages")
    with progress:
        png_paths = encode(
            input_file, output_base, config,
            on_page_complete=make_page_callback(progress, task),
            passphrase=password,
            cached_payload_hash=(payload, sha256_hash),
        )

    for p in png_paths:
        print_success(f"Saved {p}")
    console.print(f"\n[bold]Job directory: {job_dir}[/bold]")
