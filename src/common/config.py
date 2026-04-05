import struct
from dataclasses import dataclass


MAGIC = b"PCLP"
FORMAT_VERSION = 9
MARGIN_MM = 3.0

BLOCK_SIZE = 200
FINDER_PATTERN_MODULES = 7
TIMING_TRACK_WIDTH = 1
DOWNSCALE_MAX_DIM = 4000
APRILTAG_FAMILY = "tag36h11"

DOT_GAIN_FACTOR = 1.8
MIN_DOT_GAIN_FACTOR = 1.05
MAX_DOT_GAIN_FACTOR = 3.0
GUARD_BAND_PX = 1
MIN_CELL_SIZE_PX = 5
LAYOUT_CLEARANCE_DIVISOR = 200
FIDUCIAL_DPI = 300
APRILTAG_MESH_N = 32
APRILTAG_36H11_ID_COUNT = 587

QR_MODULE_PX = 12
QR_BORDER_MODULES = 2
QR_VERSION = 5

FLAG_ENCRYPTED = 0x01


def qr_image_size_px() -> int:
    modules_per_side = 17 + 4 * QR_VERSION
    return (modules_per_side + 2 * QR_BORDER_MODULES) * QR_MODULE_PX


def center_sample_half(cell_size_px: int) -> int:
    return max(1, cell_size_px // 8)


def layout_clearance_px(print_dpi: int) -> int:
    return max(3, print_dpi // LAYOUT_CLEARANCE_DIVISOR)

PAYLOAD_HEADER_REDUNDANCY = 3

HEADER_STRUCT = struct.Struct(">4sBBBBBHHHHHHI32sI")
PAYLOAD_HEADER_STRUCT = struct.Struct(">IHB")


@dataclass(frozen=True)
class PaperClipConfig:
    num_colors: int = 4
    cell_size_px: int = 28
    print_dpi: int = 1200
    rs_redundancy: float = 0.20
    redundancy_pages: int = 0
    dot_gain_factor: float = DOT_GAIN_FACTOR
    dot_guard_band_px: int = GUARD_BAND_PX
    page_width_mm: float = 210.0
    page_height_mm: float = 297.0
    margin_top_mm: float = MARGIN_MM
    margin_right_mm: float = MARGIN_MM
    margin_bottom_mm: float = MARGIN_MM
    margin_left_mm: float = MARGIN_MM


def validate_config(config: PaperClipConfig) -> PaperClipConfig:
    from common.color_picker import validate_print_ink_count

    validate_print_ink_count(config.num_colors)
    if config.cell_size_px < MIN_CELL_SIZE_PX:
        raise ValueError(f"cell_size_px must be at least {MIN_CELL_SIZE_PX}")
    if config.print_dpi < 300:
        raise ValueError("print_dpi must be at least 300")
    if config.rs_redundancy < 0.05 or config.rs_redundancy > 0.50:
        raise ValueError("rs_redundancy must be between 0.05 and 0.50")
    if config.redundancy_pages < 0:
        raise ValueError("redundancy_pages must be non-negative")
    if config.dot_gain_factor < MIN_DOT_GAIN_FACTOR or config.dot_gain_factor > MAX_DOT_GAIN_FACTOR:
        raise ValueError(
            f"dot_gain_factor must be between {MIN_DOT_GAIN_FACTOR} and {MAX_DOT_GAIN_FACTOR}",
        )
    if config.dot_guard_band_px < 0:
        raise ValueError("dot_guard_band_px must be non-negative")
    if config.cell_size_px <= 2 * config.dot_guard_band_px + 3:
        raise ValueError("dot_guard_band_px is too large for cell_size_px")
    if config.page_width_mm <= 0 or config.page_height_mm <= 0:
        raise ValueError("page dimensions must be positive")
    for name in (
        "margin_top_mm",
        "margin_right_mm",
        "margin_bottom_mm",
        "margin_left_mm",
    ):
        if getattr(config, name) < 0:
            raise ValueError(f"{name} must be non-negative")
    tw = config.page_width_mm - config.margin_left_mm - config.margin_right_mm
    th = config.page_height_mm - config.margin_top_mm - config.margin_bottom_mm
    if tw <= 0 or th <= 0:
        raise ValueError("page margins leave no usable area")
    return config


ALGO_FIELDS = (
    "num_colors",
    "cell_size_px",
    "print_dpi",
    "rs_redundancy",
    "redundancy_pages",
    "dot_gain_factor",
    "dot_guard_band_px",
)


def default_config() -> PaperClipConfig:
    return validate_config(PaperClipConfig())


def resolve_config(
    num_colors: int | None = None,
    num_symbols: int | None = None,
    cell_size_px: int | None = None,
    paper_size: str | None = None,
    print_dpi: int | None = None,
    rs_redundancy: float | None = None,
    redundancy_pages: int | None = None,
    dot_gain_factor: float | None = None,
    dot_guard_band_px: int | None = None,
    margin_mm: float | None = None,
    margin_top_mm: float | None = None,
    margin_right_mm: float | None = None,
    margin_bottom_mm: float | None = None,
    margin_left_mm: float | None = None,
) -> PaperClipConfig:
    from dataclasses import replace

    if num_colors is not None and num_symbols is not None:
        raise ValueError("pass only one of num_colors and num_symbols")
    if num_symbols is not None:
        from common.color_picker import validate_print_symbol_count

        validate_print_symbol_count(num_symbols)
        num_colors = num_symbols - 1

    base = default_config()
    overrides: dict[str, object] = {
        k: v
        for k, v in [
            ("num_colors", num_colors),
            ("cell_size_px", cell_size_px),
            ("print_dpi", print_dpi),
            ("rs_redundancy", rs_redundancy),
            ("redundancy_pages", redundancy_pages),
            ("dot_gain_factor", dot_gain_factor),
            ("dot_guard_band_px", dot_guard_band_px),
        ]
        if v is not None
    }
    if margin_mm is not None:
        overrides["margin_top_mm"] = margin_mm
        overrides["margin_right_mm"] = margin_mm
        overrides["margin_bottom_mm"] = margin_mm
        overrides["margin_left_mm"] = margin_mm
    for k, v in [
        ("margin_top_mm", margin_top_mm),
        ("margin_right_mm", margin_right_mm),
        ("margin_bottom_mm", margin_bottom_mm),
        ("margin_left_mm", margin_left_mm),
    ]:
        if v is not None:
            overrides[k] = v
    if paper_size:
        from common.paper_sizes import config_with_page_dimensions
        base = config_with_page_dimensions(base, paper_size)
    return validate_config(replace(base, **overrides) if overrides else base)


def config_from_job_dict(stored: dict) -> PaperClipConfig:
    from dataclasses import fields

    base = default_config()
    d: dict[str, object] = {f.name: getattr(base, f.name) for f in fields(PaperClipConfig)}
    for name in d:
        if name in stored:
            d[name] = stored[name]
    if "margin_mm" in stored and "margin_top_mm" not in stored:
        m = stored["margin_mm"]
        d["margin_top_mm"] = m
        d["margin_right_mm"] = m
        d["margin_bottom_mm"] = m
        d["margin_left_mm"] = m
    if "print_dpi" not in stored and "scan_dpi" in stored:
        d["print_dpi"] = stored["scan_dpi"]
    return validate_config(PaperClipConfig(**d))
