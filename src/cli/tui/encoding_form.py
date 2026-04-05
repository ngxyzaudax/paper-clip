from __future__ import annotations

from dataclasses import dataclass

from common.cell_size_picks import clamp_cell_size_pick
from common.config import PaperClipConfig, default_config, resolve_config
from common.dot_print_picks import closest_dot_gain, closest_dot_guard
from common.paper_sizes import DEFAULT_PAPER_SIZE
from common.print_dpi_presets import closest_popular_print_dpi
from common.symbols import symbol_count


def _opt_int(raw: str) -> int | None:
    s = raw.strip()
    if not s:
        return None
    return int(s)


def _opt_float(raw: str) -> float | None:
    s = raw.strip()
    if not s:
        return None
    return float(s)


@dataclass
class EncodingFormPicks:
    symbol_count: int
    cell_size_px: int
    print_dpi: int
    paper_size: str
    dot_gain_factor: float
    dot_guard_band_px: int


@dataclass(frozen=True)
class EncodingFormTextInputs:
    rs_redundancy: str
    redundancy_pages: str
    margin_top_mm: str
    margin_right_mm: str
    margin_bottom_mm: str
    margin_left_mm: str


def default_encoding_form_picks() -> EncodingFormPicks:
    dc = default_config()
    return EncodingFormPicks(
        symbol_count=symbol_count(dc.num_colors),
        cell_size_px=clamp_cell_size_pick(dc.cell_size_px),
        print_dpi=closest_popular_print_dpi(dc.print_dpi),
        paper_size=DEFAULT_PAPER_SIZE,
        dot_gain_factor=closest_dot_gain(dc.dot_gain_factor),
        dot_guard_band_px=closest_dot_guard(dc.dot_guard_band_px),
    )


def default_encoding_form_text_inputs() -> EncodingFormTextInputs:
    dc = default_config()
    return EncodingFormTextInputs(
        rs_redundancy=str(dc.rs_redundancy),
        redundancy_pages=str(dc.redundancy_pages),
        margin_top_mm=str(dc.margin_top_mm),
        margin_right_mm=str(dc.margin_right_mm),
        margin_bottom_mm=str(dc.margin_bottom_mm),
        margin_left_mm=str(dc.margin_left_mm),
    )


def resolve_encoding_form(
    picks: EncodingFormPicks,
    text: EncodingFormTextInputs,
) -> PaperClipConfig:
    return resolve_config(
        num_symbols=picks.symbol_count,
        cell_size_px=picks.cell_size_px,
        paper_size=picks.paper_size if picks.paper_size else None,
        print_dpi=picks.print_dpi,
        rs_redundancy=_opt_float(text.rs_redundancy),
        redundancy_pages=_opt_int(text.redundancy_pages),
        margin_top_mm=_opt_float(text.margin_top_mm),
        margin_right_mm=_opt_float(text.margin_right_mm),
        margin_bottom_mm=_opt_float(text.margin_bottom_mm),
        margin_left_mm=_opt_float(text.margin_left_mm),
        dot_gain_factor=picks.dot_gain_factor,
        dot_guard_band_px=picks.dot_guard_band_px,
    )
