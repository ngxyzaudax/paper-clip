from __future__ import annotations

from dataclasses import dataclass

from common.cell_size_picks import clamp_cell_size_pick
from common.symbol_count_picks import clamp_print_symbol_count
from common.config import PaperClipConfig, default_config, resolve_config
from common.paper_sizes import DEFAULT_PAPER_SIZE
from common.parity_pages_picks import closest_parity_pages
from common.print_dpi_presets import closest_popular_print_dpi
from common.rs_redundancy_picks import closest_rs_redundancy


@dataclass
class EncodingFormPicks:
    symbol_count: int
    cell_size_px: int
    print_dpi: int
    paper_size: str
    rs_redundancy: float
    redundancy_pages: int
    margin_mm: float


def default_encoding_form_picks() -> EncodingFormPicks:
    dc = default_config()
    return EncodingFormPicks(
        symbol_count=clamp_print_symbol_count(dc.num_symbols),
        cell_size_px=clamp_cell_size_pick(dc.cell_size_px),
        print_dpi=closest_popular_print_dpi(dc.print_dpi),
        paper_size=DEFAULT_PAPER_SIZE,
        rs_redundancy=closest_rs_redundancy(dc.rs_redundancy),
        redundancy_pages=closest_parity_pages(dc.redundancy_pages),
        margin_mm=dc.margin_top_mm,
    )


def resolve_encoding_form(picks: EncodingFormPicks) -> PaperClipConfig:
    return resolve_config(
        num_symbols=picks.symbol_count,
        cell_size_px=picks.cell_size_px,
        paper_size=picks.paper_size if picks.paper_size else None,
        print_dpi=picks.print_dpi,
        rs_redundancy=picks.rs_redundancy,
        redundancy_pages=picks.redundancy_pages,
        margin_mm=picks.margin_mm,
    )
