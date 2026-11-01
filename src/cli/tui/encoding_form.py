from __future__ import annotations

from dataclasses import dataclass

from calibration.profile import load_density_profile
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
    tag_size_mm: float = 4.0
    tag_pitch_mm: float = 16.0
    qr_module_mm: float = 0.36
    dot_ratio: float = 0.62


def default_encoding_form_picks() -> EncodingFormPicks:
    saved = load_density_profile()
    dc = default_config()
    if saved is None:
        return _default_picks(dc)
    return EncodingFormPicks(
        symbol_count=saved.num_symbols,
        cell_size_px=saved.cell_size_px,
        print_dpi=closest_popular_print_dpi(saved.print_dpi),
        paper_size=DEFAULT_PAPER_SIZE,
        rs_redundancy=closest_rs_redundancy(dc.rs_redundancy),
        redundancy_pages=closest_parity_pages(dc.redundancy_pages),
        margin_mm=dc.margin_top_mm,
        tag_size_mm=saved.tag_size_mm,
        tag_pitch_mm=saved.tag_pitch_mm,
        qr_module_mm=saved.qr_module_mm,
        dot_ratio=saved.dot_ratio,
    )


def _default_picks(config: PaperClipConfig) -> EncodingFormPicks:
    return EncodingFormPicks(
        symbol_count=clamp_print_symbol_count(config.num_symbols),
        cell_size_px=clamp_cell_size_pick(config.cell_size_px),
        print_dpi=closest_popular_print_dpi(config.print_dpi),
        paper_size=DEFAULT_PAPER_SIZE,
        rs_redundancy=closest_rs_redundancy(config.rs_redundancy),
        redundancy_pages=closest_parity_pages(config.redundancy_pages),
        margin_mm=config.margin_top_mm,
        tag_size_mm=config.tag_size_mm,
        tag_pitch_mm=config.tag_pitch_mm,
        qr_module_mm=config.qr_module_mm,
        dot_ratio=config.dot_ratio,
    )


_PROFILE_PICKS = (
    ("cell_size_px", "cell_size_px"),
    ("symbol_count", "num_symbols"),
    ("tag_size_mm", "tag_size_mm"),
    ("tag_pitch_mm", "tag_pitch_mm"),
    ("qr_module_mm", "qr_module_mm"),
    ("dot_ratio", "dot_ratio"),
)


def apply_profile_picks(picks: EncodingFormPicks) -> None:
    """Reset the density settings to the calibrated profile, or to defaults when none is saved."""
    source = default_encoding_form_picks()
    for pick, _ in _PROFILE_PICKS:
        setattr(picks, pick, getattr(source, pick))


def profile_source_text(picks: EncodingFormPicks) -> str:
    """One line saying whether the density settings come from calibration, defaults, or manual edits."""
    saved = load_density_profile()
    if saved is None:
        return "[dim]Density: defaults. Run Calibrate to measure your printer and scanner.[/dim]"
    if all(abs(float(getattr(picks, pick)) - float(getattr(saved, key))) < 1e-6 for pick, key in _PROFILE_PICKS):
        return "[green]Density: calibrated profile[/green]"
    return "[yellow]Density: edited; differs from the calibrated profile[/yellow]"


def resolve_encoding_form(picks: EncodingFormPicks) -> PaperClipConfig:
    return resolve_config(
        num_symbols=picks.symbol_count,
        cell_size_px=picks.cell_size_px,
        paper_size=picks.paper_size if picks.paper_size else None,
        print_dpi=picks.print_dpi,
        rs_redundancy=picks.rs_redundancy,
        redundancy_pages=picks.redundancy_pages,
        margin_mm=picks.margin_mm,
        tag_pitch_mm=picks.tag_pitch_mm,
        tag_size_mm=picks.tag_size_mm,
        qr_module_mm=picks.qr_module_mm,
        dot_ratio=picks.dot_ratio,
    )
