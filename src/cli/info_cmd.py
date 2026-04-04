from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from cli.display import config_table
from common.config import PaperClipConfig, resolve_config
from common.config_store import load_profile
from common.page_layout import (
    data_capacity_bytes,
    grid_dimensions,
    page_image_size,
    usable_area_px,
)
from common.palette import palette_from_config
from common.paper_sizes import detect_paper_size
from common.symbols import bits_per_cell, symbol_count

console = Console()


def _display_full_info(config: PaperClipConfig) -> None:
    cols, rows = grid_dimensions(config)
    pw, ph = page_image_size(config)
    uw, uh = usable_area_px(config)
    bpc = bits_per_cell(config.num_colors)
    sc = symbol_count(config.num_colors)
    capacity = data_capacity_bytes(config)

    paper_label = detect_paper_size(config.page_width_mm, config.page_height_mm)
    config_table([
        ("Paper", f"{paper_label} ({config.page_width_mm}x{config.page_height_mm}mm)"),
        ("Colors", str(config.num_colors)),
        ("Cell size", f"{config.cell_size_px} px"),
        ("Scan DPI", str(config.scan_dpi)),
        ("Margin", f"{config.margin_mm} mm"),
    ], title="Hardware Configuration")

    stats = Table(title="Encoding Statistics", show_header=True, header_style="bold cyan")
    stats.add_column("Property", style="bold")
    stats.add_column("Value")
    stats.add_row("Symbol count", str(sc))
    stats.add_row("Bits per cell", f"{bpc:.2f}")
    stats.add_row("Page image", f"{pw} x {ph} px")
    stats.add_row("Usable area", f"{uw} x {uh} px")
    stats.add_row("Data grid", f"{cols} x {rows} cells")
    stats.add_row("Total cells", f"{cols * rows:,}")
    stats.add_row("RS redundancy", f"{config.rs_redundancy:.0%}")
    stats.add_row("Capacity/page", f"{capacity:,} bytes ({capacity / 1024:.1f} KB)")
    console.print(stats)

    console.print("\n[bold]Color Palette:[/bold]")
    for i, (r, g, b) in enumerate(palette_from_config(config)):
        block = f"[on rgb({r},{g},{b})]      [/on rgb({r},{g},{b})]"
        console.print(f"  {i}: {block}  RGB({r}, {g}, {b})")


def info_command(
    profile: str | None = typer.Option(None, help="Config profile name from configs/"),
    config_file: Path | None = typer.Option(None, help="Config TOML file"),
    num_colors: int | None = typer.Option(None, help="Override num_colors"),
    cell_size_px: int | None = typer.Option(None, help="Override cell_size_px"),
    paper_size: str | None = typer.Option(None, help="Paper size (A3, A4, A5, Letter, Legal, etc.)"),
) -> None:
    """Display capacity and layout info for a configuration."""
    if profile:
        config = load_profile(profile)
        if paper_size:
            from common.paper_sizes import config_with_page_dimensions
            config = config_with_page_dimensions(config, paper_size)
    else:
        config = resolve_config(config_file, num_colors, cell_size_px, paper_size)

    _display_full_info(config)
