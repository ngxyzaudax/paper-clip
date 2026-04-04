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
from common.config import PaperClipConfig, resolve_config
from common.config_store import load_profile
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


def _resolve_config(
    profile: str | None, config_file: Path | None,
    num_colors: int | None, cell_size_px: int | None, paper_size: str | None,
) -> tuple[PaperClipConfig, str]:
    if profile:
        config = load_profile(profile)
        if paper_size:
            from dataclasses import replace
            from common.paper_sizes import paper_size_dimensions
            w, h = paper_size_dimensions(paper_size)
            config = replace(config, page_width_mm=w, page_height_mm=h)
        return config, profile
    return resolve_config(config_file, num_colors, cell_size_px, paper_size), "custom"


def encode_command(
    input_file: Path = typer.Argument(..., help="File to encode"),
    output: Path | None = typer.Option(None, help="Output path (default: data/jobs/<id>/digital/)"),
    profile: str | None = typer.Option(None, help="Config profile name from configs/"),
    config_file: Path | None = typer.Option(None, help="Config TOML file path"),
    num_colors: int | None = typer.Option(None, help="Override num_colors"),
    cell_size_px: int | None = typer.Option(None, help="Override cell_size_px"),
    paper_size: str | None = typer.Option(None, help="Paper size (A3, A4, A5, Letter, Legal, etc.)"),
    password: str | None = typer.Option(None, help="Encrypt with this password"),
    save_password: str | None = typer.Option(None, help="Save password with this label"),
) -> None:
    """Encode a file into print-ready PNG page(s). Saves into data/jobs/ by default."""
    if not input_file.exists():
        print_error(f"File not found: {input_file}")
        raise typer.Exit(1)

    config, profile_name = _resolve_config(profile, config_file, num_colors, cell_size_px, paper_size)
    from common.config import FLAG_ENCRYPTED, ALGO_FIELDS
    flags = FLAG_ENCRYPTED if password else 0

    if output is None:
        file_size = input_file.stat().st_size
        total_pages = max(1, -(-file_size // data_capacity_bytes(config)))
        config_dict = {k: getattr(config, k) for k in ALGO_FIELDS}
        job_dir = create_job(input_file.name, profile_name, config_dict, total_pages)
        output_base = digital_dir(job_dir) / "page"
        console.print(f"[cyan]Job created: {job_dir}[/cyan]\n")
    else:
        output_base = output
        job_dir = None

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

    if save_password and password:
        from common.keystore import save_password as store_pw
        store_pw(save_password, password)
        console.print(f"[cyan]Password saved as '{save_password}'[/cyan]")

    for p in png_paths:
        print_success(f"Saved {p}")
    if job_dir:
        console.print(f"\n[bold]Job directory: {job_dir}[/bold]")
