import struct
from dataclasses import dataclass

from common.cell_size_picks import validate_cell_size_pick


MAGIC = b"PCLP"
HEADER_FORMAT_VERSION = 1
MARGIN_MM = 3.56

BLOCK_SIZE = 200
TIMING_TRACK_WIDTH = 1
DOWNSCALE_MAX_DIM = 4000
APRILTAG_FAMILY = "tag36h11"

LAYOUT_CLEARANCE_DIVISOR = 200
FIDUCIAL_DPI = 300
APRILTAG_MESH_N = 5
APRILTAG_EDGE_CELLS = 9
APRILTAG_36H11_ID_COUNT = 587

QR_MODULE_PX = 12
QR_BORDER_MODULES = 2
QR_VERSION = 5


def qr_image_size_px() -> int:
    modules_per_side = 17 + 4 * QR_VERSION
    return (modules_per_side + 2 * QR_BORDER_MODULES) * QR_MODULE_PX


def center_sample_half(cell_size_px: int) -> int:
    return max(1, cell_size_px // 8)


def layout_clearance_px(print_dpi: int) -> int:
    return max(3, print_dpi // LAYOUT_CLEARANCE_DIVISOR)

PAYLOAD_HEADER_REDUNDANCY = 3

HEADER_STRUCT = struct.Struct(">4sBBBBHHHHH32sI")
PAYLOAD_HEADER_STRUCT = struct.Struct(">IHB")


@dataclass(frozen=True)
class PaperClipConfig:
    num_symbols: int = 5
    cell_size_px: int = 10
    print_dpi: int = 1200
    rs_redundancy: float = 0.20
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
    validate_cell_size_pick(config.cell_size_px)
    if config.print_dpi < 300:
        raise ValueError("print_dpi must be at least 300")
    if config.rs_redundancy < 0.05 or config.rs_redundancy > 0.50:
        raise ValueError("rs_redundancy must be between 0.05 and 0.50")
    if config.redundancy_pages < 0:
        raise ValueError("redundancy_pages must be non-negative")
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
    "num_symbols",
    "cell_size_px",
    "print_dpi",
    "rs_redundancy",
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
    from dataclasses import replace

    base = default_config()
    overrides: dict[str, object] = {
        k: v
        for k, v in [
            ("num_symbols", num_symbols),
            ("cell_size_px", cell_size_px),
            ("print_dpi", print_dpi),
            ("rs_redundancy", rs_redundancy),
            ("redundancy_pages", redundancy_pages),
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
    return validate_config(PaperClipConfig(**d))
