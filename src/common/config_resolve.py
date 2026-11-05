from dataclasses import replace

from common.config import PaperClipConfig, default_config, validate_config


def resolve_config(
    num_symbols: int | None = None,
    cell_size_px: int | None = None,
    paper_size: str | None = None,
    print_dpi: int | None = None,
    ecc_sym: int | None = None,
    redundancy_pages: int | None = None,
    margin_mm: float | None = None,
    margin_top_mm: float | None = None,
    margin_right_mm: float | None = None,
    margin_bottom_mm: float | None = None,
    margin_left_mm: float | None = None,
    tag_pitch_mm: float | None = None,
    tag_size_mm: float | None = None,
    page_width_mm: float | None = None,
    page_height_mm: float | None = None,
    qr_module_mm: float | None = None,
    dot_ratio: float | None = None,
) -> PaperClipConfig:
    base = default_config()
    overrides = _overrides(
        num_symbols, cell_size_px, print_dpi, ecc_sym, redundancy_pages,
        tag_pitch_mm, tag_size_mm, page_width_mm, page_height_mm, qr_module_mm, dot_ratio,
    )
    overrides.update(_margins(margin_mm, margin_top_mm, margin_right_mm, margin_bottom_mm, margin_left_mm))
    if paper_size:
        from common.paper_sizes import config_with_page_dimensions
        base = config_with_page_dimensions(base, paper_size)
    return validate_config(replace(base, **overrides) if overrides else base)


def _overrides(
    num_symbols: int | None,
    cell_size_px: int | None,
    print_dpi: int | None,
    ecc_sym: int | None,
    redundancy_pages: int | None,
    tag_pitch_mm: float | None,
    tag_size_mm: float | None,
    page_width_mm: float | None,
    page_height_mm: float | None,
    qr_module_mm: float | None,
    dot_ratio: float | None,
) -> dict[str, object]:
    pairs = (
        ("num_symbols", num_symbols),
        ("cell_size_px", cell_size_px),
        ("print_dpi", print_dpi),
        ("ecc_sym", ecc_sym),
        ("redundancy_pages", redundancy_pages),
        ("tag_pitch_mm", tag_pitch_mm),
        ("tag_size_mm", tag_size_mm),
        ("page_width_mm", page_width_mm),
        ("page_height_mm", page_height_mm),
        ("qr_module_mm", qr_module_mm),
        ("dot_ratio", dot_ratio),
    )
    return {key: value for key, value in pairs if value is not None}


def _margins(
    margin_mm: float | None,
    top: float | None,
    right: float | None,
    bottom: float | None,
    left: float | None,
) -> dict[str, float]:
    named = {
        "margin_top_mm": top,
        "margin_right_mm": right,
        "margin_bottom_mm": bottom,
        "margin_left_mm": left,
    }
    if margin_mm is not None:
        named = {key: margin_mm for key in named}
        named.update({key: value for key, value in (
            ("margin_top_mm", top),
            ("margin_right_mm", right),
            ("margin_bottom_mm", bottom),
            ("margin_left_mm", left),
        ) if value is not None})
    return {key: value for key, value in named.items() if value is not None}
