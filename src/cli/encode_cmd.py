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
from common.page_layout import data_capacity_bytes, grid_dimensions, page_image_size
from common.palette import palette_from_config
from common.paper_sizes import detect_paper_size
from common.symbols import bits_per_cell, symbol_count
from serialization.encode.pipeline import encode

console = Console()


def _show_encoding_plan(
    input_path: Path, output_dir: Path, config: PaperClipConfig,
) -> None:
    file_size = input_path.stat().st_size
    capacity = data_capacity_bytes(config)
    cols, rows = grid_dimensions(config)
    pw, ph = page_image_size(config)
    bpc = bits_per_cell(config.num_colors)
    sc = symbol_count(config.num_colors)
    pages = max(1, -(-file_size // capacity))
    palette = palette_from_config(config)
    paper_name = detect_paper_size(config.page_width_mm, config.page_height_mm)
    config_table([
        ("Paper", f"{paper_name} ({config.page_width_mm}x{config.page_height_mm}mm)"),
        ("Colors", str(config.num_colors)),
        ("Cell size", f"{config.cell_size_px} px"),
        ("Symbols", str(sc)),
        ("Bits/cell", f"{bpc:.2f}"),
        ("Grid", f"{cols} x {rows} cells"),
        ("Page image", f"{pw} x {ph} px"),
        ("RS redundancy", f"{config.rs_redundancy:.0%}"),
    ], title="Encoding Configuration")
    console.print("\n[bold]Color Palette:[/bold]")
    for i, (r, g, b) in enumerate(palette):
        block = f"[on rgb({r},{g},{b})]      [/on rgb({r},{g},{b})]"
        console.print(f"  {i}: {block}  RGB({r}, {g}, {b})")
    summary = Table(title="\nEncoding Plan", show_header=True, header_style="bold cyan")
    summary.add_column("Detail", style="bold")
    summary.add_column("Value", style="white")
    summary.add_row("Input file", str(input_path))
    summary.add_row("File size", file_size_display(file_size))
    summary.add_row("Capacity/page", file_size_display(capacity))
    summary.add_row("Pages needed", str(pages))
    utilization = min(100.0, (file_size / (capacity * pages)) * 100)
    summary.add_row("Space utilization", f"{utilization:.1f}%")
    summary.add_row("Output", str(output_dir))
    console.print(summary)


def encode_command(
    input_file: Path = typer.Argument(..., help="File to encode"),
    config_file: Path | None = typer.Option(None, "--config", help="Base settings from this TOML file"),
    num_colors: int | None = typer.Option(None, help="Number of symbol colors"),
    cell_size_px: int | None = typer.Option(None, help="Cell size in pixels"),
    paper_size: str | None = typer.Option(None, help="Paper size (A3, A4, A5, Letter, Legal, etc.)"),
    print_dpi: int | None = typer.Option(None, help="Logical page DPI for layout and print hints"),
    rs_redundancy: float | None = typer.Option(None, help="Reed–Solomon redundancy (0.05–0.50)"),
    redundancy_pages: int | None = typer.Option(None, help="Extra parity pages (fountain)"),
    margin_mm: float | None = typer.Option(None, help="Uniform page margin in mm (all sides)"),
    margin_top_mm: float | None = typer.Option(None, help="Top page margin in mm"),
    margin_right_mm: float | None = typer.Option(None, help="Right page margin in mm"),
    margin_bottom_mm: float | None = typer.Option(None, help="Bottom page margin in mm"),
    margin_left_mm: float | None = typer.Option(None, help="Left page margin in mm"),
    password: str | None = typer.Option(None, help="Encrypt with this password"),
) -> None:
    """Encode a file into print-ready PNG page(s). Saves into data/jobs/ by default."""
    if not input_file.exists():
        print_error(f"File not found: {input_file}")
        raise typer.Exit(1)

    config = cli_encoding_config(
        config_file, num_colors, cell_size_px, paper_size,
        print_dpi, rs_redundancy, redundancy_pages, margin_mm,
        margin_top_mm, margin_right_mm, margin_bottom_mm, margin_left_mm,
    )
    from common.config import FLAG_ENCRYPTED

    flags = FLAG_ENCRYPTED if password else 0

    file_size = input_file.stat().st_size
    total_pages = max(1, -(-file_size // data_capacity_bytes(config)))
    config_dict = {k: getattr(config, k) for k in ALGO_FIELDS}
    for k in (
        "margin_top_mm",
        "margin_right_mm",
        "margin_bottom_mm",
        "margin_left_mm",
    ):
        config_dict[k] = getattr(config, k)
    job_dir = create_job(input_file.name, "inline", config_dict, total_pages)
    output_base = digital_dir(job_dir) / "page"
    console.print(f"[cyan]Job created: {job_dir}[/cyan]\n")

    _show_encoding_plan(input_file, output_base.parent, config)
    if password:
        console.print("[bold yellow]Encryption enabled[/bold yellow]")
    console.print()

    progress, task = make_page_progress("Rendering pages")
    with progress:
        png_paths = encode(
            input_file, output_base, config,
            on_page_complete=make_page_callback(progress, task),
            flags=flags, passphrase=password,
        )

    for p in png_paths:
        print_success(f"Saved {p}")
    console.print(f"\n[bold]Job directory: {job_dir}[/bold]")
