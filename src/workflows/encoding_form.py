from __future__ import annotations

from dataclasses import dataclass

from calibration.profile import load_density_profile
from common.cell_size_picks import clamp_cell_size_pick
from common.config import PaperClipConfig, default_config, resolve_config
from common.ecc_sym_picks import closest_ecc_sym
from common.paper_sizes import DEFAULT_PAPER_SIZE
from common.parity_pages_picks import closest_parity_pages
from common.print_dpi_presets import closest_popular_print_dpi
from common.symbol_count_picks import clamp_print_symbol_count
from serialization.encode.fill_sheets import FILL_PRIORITIES, SheetPlan


@dataclass
class EncodingFormPicks:
    symbol_count: int
    cell_size_px: int
    print_dpi: int
    paper_size: str
    ecc_sym: int
    redundancy_pages: int
    margin_mm: float
    tag_size_mm: float = 4.0
    tag_pitch_mm: float = 16.0
    qr_module_mm: float = 0.36
    dot_ratio: float = 0.62
    sides: int = 1
    fill_sheets: bool = True
    sheets: int = 0
    fill_priority: str = "protection"


_PROFILE_PICKS = (
    ("cell_size_px", "cell_size_px"),
    ("symbol_count", "num_symbols"),
    ("tag_size_mm", "tag_size_mm"),
    ("tag_pitch_mm", "tag_pitch_mm"),
    ("qr_module_mm", "qr_module_mm"),
    ("dot_ratio", "dot_ratio"),
)


def default_encoding_form_picks() -> EncodingFormPicks:
    saved = load_density_profile()
    config = default_config()
    if saved is None:
        return _default_picks(config)
    return EncodingFormPicks(
        symbol_count=saved.num_symbols,
        cell_size_px=saved.cell_size_px,
        print_dpi=closest_popular_print_dpi(saved.print_dpi),
        paper_size=DEFAULT_PAPER_SIZE,
        ecc_sym=closest_ecc_sym(config.ecc_sym),
        redundancy_pages=closest_parity_pages(config.redundancy_pages),
        margin_mm=config.margin_top_mm,
        tag_size_mm=saved.tag_size_mm,
        tag_pitch_mm=saved.tag_pitch_mm,
        qr_module_mm=saved.qr_module_mm,
        dot_ratio=saved.dot_ratio,
    )


def profile_source(picks: EncodingFormPicks) -> str:
    saved = load_density_profile()
    if saved is None:
        return "defaults"
    matched = all(abs(float(getattr(picks, pick)) - float(getattr(saved, key))) < 1e-6 for pick, key in _PROFILE_PICKS)
    return "profile" if matched else "edited"


def resolve_encoding_form(picks: EncodingFormPicks) -> PaperClipConfig:
    return resolve_config(
        num_symbols=picks.symbol_count,
        cell_size_px=picks.cell_size_px,
        paper_size=picks.paper_size if picks.paper_size else None,
        print_dpi=picks.print_dpi,
        ecc_sym=picks.ecc_sym,
        redundancy_pages=picks.redundancy_pages,
        margin_mm=picks.margin_mm,
        tag_pitch_mm=picks.tag_pitch_mm,
        tag_size_mm=picks.tag_size_mm,
        qr_module_mm=picks.qr_module_mm,
        dot_ratio=picks.dot_ratio,
    )


def sheet_plan(picks: EncodingFormPicks) -> SheetPlan:
    priority = picks.fill_priority if picks.fill_priority in FILL_PRIORITIES else "protection"
    return SheetPlan(2 if picks.sides == 2 else 1, picks.fill_sheets, max(0, picks.sheets), priority)


def _default_picks(config: PaperClipConfig) -> EncodingFormPicks:
    return EncodingFormPicks(
        symbol_count=clamp_print_symbol_count(config.num_symbols),
        cell_size_px=clamp_cell_size_pick(config.cell_size_px),
        print_dpi=closest_popular_print_dpi(config.print_dpi),
        paper_size=DEFAULT_PAPER_SIZE,
        ecc_sym=closest_ecc_sym(config.ecc_sym),
        redundancy_pages=closest_parity_pages(config.redundancy_pages),
        margin_mm=config.margin_top_mm,
        tag_size_mm=config.tag_size_mm,
        tag_pitch_mm=config.tag_pitch_mm,
        qr_module_mm=config.qr_module_mm,
        dot_ratio=config.dot_ratio,
    )
