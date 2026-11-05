from calibration.profile import DensityProfile, load_density_profile
from common.config import PaperClipConfig, resolve_config


def cli_encoding_config(
    num_symbols: int | None,
    cell_size_px: int | None,
    paper_size: str | None,
    print_dpi: int | None,
    ecc_sym: int | None,
    redundancy_pages: int | None,
    margin_mm: float | None = None,
    margin_top_mm: float | None = None,
    margin_right_mm: float | None = None,
    margin_bottom_mm: float | None = None,
    margin_left_mm: float | None = None,
    tag_pitch_mm: float | None = None,
    tag_size_mm: float | None = None,
    qr_module_mm: float | None = None,
    dot_ratio: float | None = None,
) -> PaperClipConfig:
    saved = load_density_profile()
    return resolve_config(
        num_symbols=_or(num_symbols, saved, "num_symbols"),
        cell_size_px=_or(cell_size_px, saved, "cell_size_px"),
        paper_size=paper_size,
        print_dpi=_or(print_dpi, saved, "print_dpi"),
        ecc_sym=ecc_sym,
        redundancy_pages=redundancy_pages,
        margin_mm=margin_mm,
        margin_top_mm=margin_top_mm,
        margin_right_mm=margin_right_mm,
        margin_bottom_mm=margin_bottom_mm,
        margin_left_mm=margin_left_mm,
        tag_pitch_mm=_or(tag_pitch_mm, saved, "tag_pitch_mm"),
        tag_size_mm=_or(tag_size_mm, saved, "tag_size_mm"),
        qr_module_mm=_or(qr_module_mm, saved, "qr_module_mm"),
        dot_ratio=_or(dot_ratio, saved, "dot_ratio"),
    )


def _or(
    explicit: int | float | None, saved: DensityProfile | None, name: str,
) -> int | float | None:
    if explicit is not None:
        return explicit
    if saved is None:
        return None
    value = getattr(saved, name)
    return value if isinstance(value, (int, float)) else None
