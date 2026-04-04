import struct
from dataclasses import dataclass
from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib

import tomli_w


MAGIC = b"PCLP"
FORMAT_VERSION = 8
MARGIN_MM = 3.0

BLOCK_SIZE = 200
FINDER_PATTERN_MODULES = 7
TIMING_TRACK_WIDTH = 1
DOWNSCALE_MAX_DIM = 4000
APRILTAG_FAMILY = "tag36h11"

DOT_GAIN_FACTOR = 1.8
GUARD_BAND_PX = 1
MIN_CELL_SIZE_PX = 5
LAYOUT_CLEARANCE_DIVISOR = 200

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
    page_width_mm: float = 210.0
    page_height_mm: float = 297.0
    margin_top_mm: float = MARGIN_MM
    margin_right_mm: float = MARGIN_MM
    margin_bottom_mm: float = MARGIN_MM
    margin_left_mm: float = MARGIN_MM


def validate_config(config: PaperClipConfig) -> PaperClipConfig:
    if config.num_colors < 2:
        raise ValueError("num_colors must be at least 2")
    if config.cell_size_px < MIN_CELL_SIZE_PX:
        raise ValueError(f"cell_size_px must be at least {MIN_CELL_SIZE_PX}")
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


ALGO_FIELDS = ("num_colors", "cell_size_px", "print_dpi", "rs_redundancy", "redundancy_pages")


def save_config(config: PaperClipConfig, path: Path) -> None:
    data = {"paper_clip": {k: getattr(config, k) for k in ALGO_FIELDS}}
    path.write_bytes(tomli_w.dumps(data).encode())


def load_config(path: Path) -> PaperClipConfig:
    raw = tomllib.loads(path.read_text())
    section = dict(raw.get("paper_clip", {}))
    if "print_dpi" not in section and "scan_dpi" in section:
        section["print_dpi"] = section["scan_dpi"]
    if "margin_mm" in section and "margin_top_mm" not in section:
        m = section.pop("margin_mm")
        section["margin_top_mm"] = m
        section["margin_right_mm"] = m
        section["margin_bottom_mm"] = m
        section["margin_left_mm"] = m
    valid_fields = {f.name for f in __import__("dataclasses").fields(PaperClipConfig)}
    filtered = {k: v for k, v in section.items() if k in valid_fields}
    return validate_config(PaperClipConfig(**filtered))


def default_config() -> PaperClipConfig:
    return validate_config(PaperClipConfig())


def resolve_config(
    config_file: Path | None = None,
    num_colors: int | None = None,
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

    base = load_config(config_file) if config_file else default_config()
    overrides: dict[str, object] = {
        k: v
        for k, v in [
            ("num_colors", num_colors),
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
    if "margin_mm" in stored and "margin_top_mm" not in stored:
        m = stored["margin_mm"]
        d["margin_top_mm"] = m
        d["margin_right_mm"] = m
        d["margin_bottom_mm"] = m
        d["margin_left_mm"] = m
    if "print_dpi" not in stored and "scan_dpi" in stored:
        d["print_dpi"] = stored["scan_dpi"]
    return validate_config(PaperClipConfig(**d))
