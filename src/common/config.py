from dataclasses import dataclass, fields

from common.format_spec import (
    DEFAULT_ECC_SYM,
    DEFAULT_MARGIN_MM,
    DOT_DIAMETER_RATIO,
    ECC_MAX,
    ECC_MIN,
    MIN_CELL_MM,
    MIN_MARGIN_MM,
    QR_MODULE_MM,
    TAG_PITCH_MAX_MM,
    TAG_PITCH_MIN_MM,
    TAG_TARGET_PITCH_MM,
)
from common.density_preset import CELL_HOLD_PX, TAG_HOLD_MM
from common.dot_ratio import dot_ratio_index
from common.qr_scale import qr_scale_index
from common.tag_scale import tag_scale_index

MARGIN_MM = DEFAULT_MARGIN_MM


@dataclass(frozen=True)
class PaperClipConfig:
    num_symbols: int = 5
    cell_size_px: int = CELL_HOLD_PX
    print_dpi: int = 720
    ecc_sym: int = DEFAULT_ECC_SYM
    tag_pitch_mm: float = TAG_TARGET_PITCH_MM
    tag_size_mm: float = TAG_HOLD_MM
    redundancy_pages: int = 0
    page_width_mm: float = 210.0
    page_height_mm: float = 297.0
    margin_top_mm: float = MARGIN_MM
    margin_right_mm: float = MARGIN_MM
    margin_bottom_mm: float = MARGIN_MM
    margin_left_mm: float = MARGIN_MM
    qr_module_mm: float = QR_MODULE_MM
    dot_ratio: float = DOT_DIAMETER_RATIO


def validate_config(config: PaperClipConfig) -> PaperClipConfig:
    from common.color_picker import validate_print_symbol_count

    validate_print_symbol_count(config.num_symbols)
    _validate_cell(config)
    if config.print_dpi < 300:
        raise ValueError("print_dpi must be at least 300")
    if not ECC_MIN <= config.ecc_sym <= ECC_MAX:
        raise ValueError(f"ecc_sym must be between {ECC_MIN} and {ECC_MAX}")
    tag_scale_index(config.tag_size_mm)
    qr_scale_index(config.qr_module_mm)
    dot_ratio_index(config.dot_ratio)
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
    "ecc_sym",
    "tag_pitch_mm",
    "tag_size_mm",
    "redundancy_pages",
    "qr_module_mm",
    "dot_ratio",
)


def default_config() -> PaperClipConfig:
    return validate_config(PaperClipConfig())


def __getattr__(name: str) -> object:
    if name == "resolve_config":
        from common.config_resolve import resolve_config
        return resolve_config
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def config_from_job_dict(stored: dict) -> PaperClipConfig:
    base = default_config()
    values: dict[str, object] = {item.name: getattr(base, item.name) for item in fields(PaperClipConfig)}
    for name in values:
        if name in stored:
            values[name] = stored[name]
    return validate_config(PaperClipConfig(**values))
