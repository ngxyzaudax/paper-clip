from pathlib import Path

from rich.console import Console
from rich.table import Table

from cli.display import config_table, file_size_display
from common.config import PaperClipConfig
from common.page_layout import data_capacity_bytes, grid_dimensions, page_image_size, pages_needed
from common.palette import palette_from_config
from common.paper_sizes import detect_paper_size
from common.symbols import bits_per_cell

console = Console()


def show_encoding_plan(
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
    _print_swatch(0, (255, 255, 255), "blank paper, no dot")
    for symbol, colour in enumerate(palette, start=1):
        _print_swatch(symbol, colour, "")
    _print_summary(input_path, output_dir, source_file_size, payload_size, capacity, data_pages, pages)


def _print_swatch(symbol: int, colour: tuple[int, int, int], note: str) -> None:
    red, green, blue = colour
    block = f"[on rgb({red},{green},{blue})]      [/on rgb({red},{green},{blue})]"
    suffix = f"  ({note})" if note else ""
    console.print(f"  {symbol}: {block}  RGB({red}, {green}, {blue}){suffix}")


def _print_summary(
    input_path: Path,
    output_dir: Path,
    source_file_size: int,
    payload_size: int,
    capacity: int,
    data_pages: int,
    pages: int,
) -> None:
    summary = Table(title="\nEncoding Plan", show_header=True, header_style="bold cyan")
    summary.add_column("Detail", style="bold")
    summary.add_column("Value", style="white")
    summary.add_row("Input file", str(input_path))
    summary.add_row("File size", file_size_display(source_file_size))
    summary.add_row("Payload size", file_size_display(payload_size))
    summary.add_row("Capacity/page", file_size_display(capacity))
    summary.add_row("Data pages", str(data_pages))
    summary.add_row("Total pages", str(pages))
    utilization = (payload_size / (capacity * data_pages)) * 100 if data_pages > 0 else 0.0
    summary.add_row("Space utilization", f"{min(100.0, utilization):.1f}%")
    summary.add_row("Output", str(output_dir))
    console.print(summary)
