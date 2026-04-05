from common.config import PaperClipConfig, resolve_config


def cli_encoding_config(
    num_symbols: int | None,
    cell_size_px: int | None,
    paper_size: str | None,
    print_dpi: int | None,
    rs_redundancy: float | None,
    redundancy_pages: int | None,
    margin_mm: float | None = None,
    margin_top_mm: float | None = None,
    margin_right_mm: float | None = None,
    margin_bottom_mm: float | None = None,
    margin_left_mm: float | None = None,
    dot_gain_factor: float | None = None,
    dot_guard_band_px: int | None = None,
) -> PaperClipConfig:
    return resolve_config(
        num_symbols=num_symbols,
        cell_size_px=cell_size_px,
        paper_size=paper_size,
        print_dpi=print_dpi,
        rs_redundancy=rs_redundancy,
        redundancy_pages=redundancy_pages,
        dot_gain_factor=dot_gain_factor,
        dot_guard_band_px=dot_guard_band_px,
        margin_mm=margin_mm,
        margin_top_mm=margin_top_mm,
        margin_right_mm=margin_right_mm,
        margin_bottom_mm=margin_bottom_mm,
        margin_left_mm=margin_left_mm,
    )
