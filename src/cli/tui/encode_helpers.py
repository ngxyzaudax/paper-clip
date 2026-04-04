from pathlib import Path

from common.config import PaperClipConfig
from common.page_layout import data_capacity_bytes, grid_dimensions
from common.symbols import bits_per_cell


def format_config_details(config: PaperClipConfig) -> str:
    cols, rows = grid_dimensions(config)
    cap = data_capacity_bytes(config)
    return (
        f"Colors: {config.num_colors}  |  Cell: {config.cell_size_px}px  |  "
        f"Grid: {cols}x{rows}  |  Bits/cell: {bits_per_cell(config.num_colors):.2f}\n"
        f"RS redundancy: {config.rs_redundancy:.0%}  |  "
        f"Capacity: [bold]{cap:,}[/bold] bytes/page ({cap / 1024:.1f} KB)"
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
