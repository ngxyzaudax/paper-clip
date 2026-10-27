from dataclasses import dataclass, fields, replace

from common.format_spec import (
    BLOCK_SIZE,
    DEFAULT_MARGIN_MM,
    MIN_CELL_MM,
    MIN_MARGIN_MM,
    TAG_PITCH_MAX_MM,
    TAG_PITCH_MIN_MM,
    TAG_TARGET_PITCH_MM,
)

MARGIN_MM = DEFAULT_MARGIN_MM


@dataclass(frozen=True)
class PaperClipConfig:
    num_symbols: int = 5
    cell_size_px: int = 32
    print_dpi: int = 720
    rs_redundancy: float = 0.45
    tag_pitch_mm: float = TAG_TARGET_PITCH_MM
    redundancy_pages: int = 0
    page_width_mm: float = 210.0
    page_height_mm: float = 297.0
    margin_top_mm: float = MARGIN_MM
    margin_right_mm: float = MARGIN_MM
    margin_bottom_mm: float = MARGIN_MM
    margin_left_mm: float = MARGIN_MM


def validate_config(config: PaperClipConfig) -> PaperClipConfig:
    from common.color_picker import validate_print_symbol_count

    validate_print_symbol_count(config.num_symbols)
    _validate_cell(config)
    if config.print_dpi < 300:
        raise ValueError("print_dpi must be at least 300")
    if config.rs_redundancy < 0.05 or config.rs_redundancy > 0.50:
        raise ValueError("rs_redundancy must be between 0.05 and 0.50")
    if config.tag_pitch_mm < TAG_PITCH_MIN_MM or config.tag_pitch_mm > TAG_PITCH_MAX_MM:
        raise ValueError(
            f"tag_pitch_mm must be between {TAG_PITCH_MIN_MM:.0f} and {TAG_PITCH_MAX_MM:.0f}"
        )
    if config.redundancy_pages < 0:
        raise ValueError("redundancy_pages must be non-negative")
    if config.page_width_mm <= 0 or config.page_height_mm <= 0:
        raise ValueError("page dimensions must be positive")
    for name in ("margin_top_mm", "margin_right_mm", "margin_bottom_mm", "margin_left_mm"):
        if getattr(config, name) < MIN_MARGIN_MM:
            raise ValueError(
                f"{name} must be at least {MIN_MARGIN_MM:g} mm; paper-clip pages are never printed borderless"
            )
    usable_w = config.page_width_mm - config.margin_left_mm - config.margin_right_mm
    usable_h = config.page_height_mm - config.margin_top_mm - config.margin_bottom_mm
    if usable_w <= 0 or usable_h <= 0:
        raise ValueError("page margins leave no usable area")
    return config


def _validate_cell(config: PaperClipConfig) -> None:
    px = config.cell_size_px
    if px < 8 or px > 160:
        raise ValueError(f"cell_size_px must be between 8 and 160; got {px}")
    mm = px * 25.4 / config.print_dpi
    if mm < MIN_CELL_MM:
        raise ValueError(
            f"cell size {mm:.3f} mm is below the {MIN_CELL_MM} mm minimum at {config.print_dpi} dpi"
        )


ALGO_FIELDS = (
    "num_symbols",
    "cell_size_px",
    "print_dpi",
    "rs_redundancy",
    "tag_pitch_mm",
    "redundancy_pages",
)


def default_config() -> PaperClipConfig:
    return validate_config(PaperClipConfig())


def resolve_config(
    num_symbols: int | None = None,
    cell_size_px: int | None = None,
    paper_size: str | None = None,
    print_dpi: int | None = None,
    rs_redundancy: float | None = None,
    redundancy_pages: int | None = None,
    margin_mm: float | None = None,
    margin_top_mm: float | None = None,
    margin_right_mm: float | None = None,
    margin_bottom_mm: float | None = None,
    margin_left_mm: float | None = None,
) -> PaperClipConfig:
    base = default_config()
    overrides: dict[str, object] = {
        key: value
        for key, value in (
            ("num_symbols", num_symbols),
            ("cell_size_px", cell_size_px),
            ("print_dpi", print_dpi),
            ("rs_redundancy", rs_redundancy),
            ("redundancy_pages", redundancy_pages),
        )
        if value is not None
    }
    if margin_mm is not None:
        overrides["margin_top_mm"] = margin_mm
        overrides["margin_right_mm"] = margin_mm
        overrides["margin_bottom_mm"] = margin_mm
        overrides["margin_left_mm"] = margin_mm
    for key, value in (
        ("margin_top_mm", margin_top_mm),
        ("margin_right_mm", margin_right_mm),
        ("margin_bottom_mm", margin_bottom_mm),
        ("margin_left_mm", margin_left_mm),
    ):
        if value is not None:
            overrides[key] = value
    if paper_size:
        from common.paper_sizes import config_with_page_dimensions
        base = config_with_page_dimensions(base, paper_size)
    return validate_config(replace(base, **overrides) if overrides else base)


def config_from_job_dict(stored: dict) -> PaperClipConfig:
    base = default_config()
    values: dict[str, object] = {item.name: getattr(base, item.name) for item in fields(PaperClipConfig)}
    for name in values:
        if name in stored:
            values[name] = stored[name]
    return validate_config(PaperClipConfig(**values))
