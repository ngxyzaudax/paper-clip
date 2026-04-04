from pathlib import Path

from common.config import PaperClipConfig
from common.page_layout import data_capacity_bytes, grid_dimensions, page_image_size, usable_area_px
from common.palette import palette_from_config
from common.symbols import bits_per_cell, symbol_count

_PALETTE_PREVIEW_MAX_COLORS = 48


def _format_rgb_display(r: int, g: int, b: int) -> str:
    return f"{r:>3},{g:>3},{b:>3}"


def _palette_index_width(palette_len: int) -> int:
    if palette_len <= 0:
        return 2
    return max(2, len(str(palette_len - 1)))


def _palette_swatch_line(
    index: int, rgb: tuple[int, int, int], idx_width: int,
) -> str:
    r, g, b = rgb
    idx_s = f"[{index:0{idx_width}d}]"
    return f"{idx_s} [on rgb({r},{g},{b})]  [/on rgb({r},{g},{b})] {_format_rgb_display(r, g, b)}"


def _format_palette_two_columns(palette: list[tuple[int, int, int]]) -> str:
    w = _palette_index_width(len(palette))
    lines: list[str] = []
    for i in range(0, len(palette), 2):
        left = _palette_swatch_line(i, palette[i], w)
        if i + 1 < len(palette):
            right = _palette_swatch_line(i + 1, palette[i + 1], w)
            lines.append(f"  {left}  |  {right}")
        else:
            lines.append(f"  {left}")
    return "\n".join(lines)


def format_encoding_info_panel(config: PaperClipConfig, paper_size: str) -> str:
    cols, rows = grid_dimensions(config)
    pw, ph = page_image_size(config)
    uw, uh = usable_area_px(config)
    bpc = bits_per_cell(config.num_colors)
    sc = symbol_count(config.num_colors)
    capacity = data_capacity_bytes(config)
    if config.num_colors <= _PALETTE_PREVIEW_MAX_COLORS:
        palette = palette_from_config(config)
        palette_lines = _format_palette_two_columns(palette)
    else:
        palette_lines = f"  ({config.num_colors} colors; preview omitted in TUI)"
    return (
        f"[bold cyan]Encoding Parameters[/bold cyan]\n"
        f"  Colors: {config.num_colors}    Cell: {config.cell_size_px}px\n"
        f"  Symbols: {sc}    Bits/cell: {bpc:.2f}    RS redundancy: {config.rs_redundancy:.0%}\n\n"
        f"[bold cyan]Hardware[/bold cyan]\n"
        f"  Print DPI: {config.print_dpi}    Margins mm T/R/B/L: "
        f"{config.margin_top_mm}/{config.margin_right_mm}/"
        f"{config.margin_bottom_mm}/{config.margin_left_mm}\n"
        f"  Paper: {paper_size} ({config.page_width_mm}x{config.page_height_mm}mm, {pw}x{ph}px)\n"
        f"  Usable area: {uw}x{uh}px\n\n"
        f"[bold cyan]Capacity[/bold cyan]\n"
        f"  Grid: {cols}x{rows} = {cols * rows:,} cells\n"
        f"  Capacity/page: [bold]{capacity:,}[/bold] bytes ({capacity / 1024:.1f} KB)\n\n"
        f"[bold cyan]Color Palette[/bold cyan]\n"
        f"{palette_lines}"
    )


def format_encoding_plan(
    config: PaperClipConfig, input_path: Path,
) -> str:
    sz = input_path.stat().st_size
    cap = data_capacity_bytes(config)
    pages = max(1, -(-sz // cap))
    return (
        f"[bold]Encoding Plan:[/bold]  {input_path.name} ({sz:,} B)\n"
        f"Pages: {pages}  |  Utilization: {min(100.0, sz / (cap * pages) * 100):.1f}%  |  "
        f"Output: data/jobs/..."
    )
