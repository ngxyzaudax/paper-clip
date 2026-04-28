import logging
from pathlib import Path

from common.codec import rs_encoded_stream_data_vs_parity
from common.config import BLOCK_SIZE, PaperClipConfig
from common.perf import log_phase
from common.page_layout import data_capacity_bytes, grid_dimensions, page_image_size, usable_area_px
from common.color_picker import symbol_option_label
from common.palette import palette_from_config
from common.symbols import bits_per_cell

_PALETTE_PREVIEW_MAX_COLORS = 48


def _format_rgb_display(r: int, g: int, b: int) -> str:
    return f"{r:>3},{g:>3},{b:>3}"


def _symbol_label_width(max_symbol: int) -> int:
    if max_symbol <= 0:
        return 2
    return max(2, len(str(max_symbol)))


def _palette_swatch_line(
    symbol: int, rgb: tuple[int, int, int], label_width: int,
) -> str:
    r, g, b = rgb
    lab = f"[{symbol:0{label_width}d}]"
    return f"{lab} [on rgb({r},{g},{b})]  [/on rgb({r},{g},{b})] {_format_rgb_display(r, g, b)}"


def _format_palette_two_columns(palette: list[tuple[int, int, int]]) -> str:
    w = _symbol_label_width(len(palette))
    lines: list[str] = []
    for i in range(0, len(palette), 2):
        left = _palette_swatch_line(i + 1, palette[i], w)
        if i + 1 < len(palette):
            right = _palette_swatch_line(i + 2, palette[i + 1], w)
            lines.append(f"  {left}  |  {right}")
        else:
            lines.append(f"  {left}")
    return "\n".join(lines)


def format_encoding_info_panel(config: PaperClipConfig, paper_size: str) -> str:
    logger = logging.getLogger(__name__)
    with log_phase(logger, "tui.format_encoding_info_panel"):
        return _format_encoding_info_panel_body(config, paper_size)


def _format_encoding_info_panel_body(config: PaperClipConfig, paper_size: str) -> str:
    cols, rows = grid_dimensions(config)
    pw, ph = page_image_size(config)
    uw, uh = usable_area_px(config)
    bpc = bits_per_cell(config.num_symbols)
    sc = config.num_symbols
    capacity = data_capacity_bytes(config)
    data_cap, ecc_cap = rs_encoded_stream_data_vs_parity(
        capacity, BLOCK_SIZE, config.rs_redundancy,
    )
    if config.num_symbols <= _PALETTE_PREVIEW_MAX_COLORS:
        palette = palette_from_config(config)
        w = _symbol_label_width(len(palette))
        palette_lines = (
            "  " + _palette_swatch_line(0, (255, 255, 255), w) + "\n"
            + _format_palette_two_columns(palette)
        )
    else:
        palette_lines = f"  ({sc} symbols; preview omitted in TUI)"
    mt, mr, mb, ml = (
        config.margin_top_mm,
        config.margin_right_mm,
        config.margin_bottom_mm,
        config.margin_left_mm,
    )
    if mt == mr == mb == ml:
        margins_line = f"  Margins: {mt:g} mm (all sides)\n"
    else:
        margins_line = f"  Margins mm T/R/B/L: {mt}/{mr}/{mb}/{ml}\n"
    return (
        f"[bold cyan]Encoding Parameters[/bold cyan]\n"
        f"  {symbol_option_label(sc)}    Cell: {config.cell_size_px}px\n"
        f"  Dot gain: {config.dot_gain_factor}    Dot guard: {config.dot_guard_band_px}px\n"
        f"  Bits/cell: {bpc:.2f}    RS redundancy: {config.rs_redundancy:.0%}\n\n"
        f"[bold cyan]Hardware[/bold cyan]\n"
        f"  Print DPI: {config.print_dpi}\n"
        f"{margins_line}"
        f"  Paper: {paper_size} ({config.page_width_mm}x{config.page_height_mm}mm, {pw}x{ph}px)\n"
        f"  Usable area: {uw}x{uh}px\n\n"
        f"[bold cyan]Capacity[/bold cyan]\n"
        f"  {cols}x{rows} ({cols * rows:,} cells)\n"
        f"  Total: {capacity:,} B\n"
        f"  Data: {data_cap:,} B\n"
        f"  ERR_C: {ecc_cap:,} B\n\n"
        f"[bold cyan]Symbol palette[/bold cyan]\n"
        f"{palette_lines}"
    )


def format_encoding_plan(
    config: PaperClipConfig,
    input_path: Path,
    passphrase: str | None = None,
) -> str:
    from serialization.encode.encoder import payload_byte_length_and_hash

    from common.page_layout import pages_needed

    logger = logging.getLogger(__name__)
    with log_phase(logger, "tui.encoding_plan.read_input"):
        raw = input_path.read_bytes()
    sz = len(raw)
    with log_phase(logger, "tui.encoding_plan.payload_byte_length"):
        plen, _ = payload_byte_length_and_hash(
            raw, config, filename=input_path.name, passphrase=passphrase,
        )
    cap = data_capacity_bytes(config)
    data_pages = pages_needed(plen, config)
    total_pages = data_pages + config.redundancy_pages
    util = (
        min(100.0, plen / (cap * data_pages) * 100) if data_pages > 0 and cap > 0 else 0.0
    )
    return (
        f"[bold]Encoding Plan:[/bold]  {input_path.name}  file {sz:,} B  payload {plen:,} B\n"
        f"Data pages: {data_pages}  total {total_pages}  |  Utilization: {util:.1f}%  |  "
        f"Output: data/jobs/..."
    )
