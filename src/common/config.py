import struct
from dataclasses import dataclass
from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib

import tomli_w


MAGIC = b"PCLP"
FORMAT_VERSION = 5
MARGIN_MM = 3.0

BLOCK_SIZE = 200
FINDER_PATTERN_MODULES = 7
CALIBRATION_BAR_ROWS = 3
TIMING_TRACK_WIDTH = 1
DOWNSCALE_MAX_DIM = 4000
APRILTAG_FAMILY = "tag36h11"

DOT_GAIN_FACTOR = 1.8
GUARD_BAND_PX = 1
MIN_CELL_SIZE_PX = 12

QR_MODULE_PX = 12
QR_BORDER_MODULES = 4
QR_VERSION = 5

FLAG_ENCRYPTED = 0x01
FLAG_HAS_PALETTE_QR = 0x02

PALETTE_QR_MODULE_PX = 10
PALETTE_QR_BORDER = 2

_PALETTE_QR_EC_M_CAPACITY = [0, 14, 26, 42, 62, 84, 106, 122, 152, 180, 213]


def palette_qr_image_size_px(num_colors: int) -> int:
    if num_colors <= 0:
        return 0
    raw_size = 9 + 3 * num_colors
    b64_size = ((raw_size + 2) // 3) * 4
    version = 0
    for v, cap in enumerate(_PALETTE_QR_EC_M_CAPACITY):
        if cap >= b64_size:
            version = v
            break
    else:
        version = len(_PALETTE_QR_EC_M_CAPACITY) - 1
    modules = 17 + 4 * version
    return (modules + 2 * PALETTE_QR_BORDER) * PALETTE_QR_MODULE_PX


def qr_image_size_px() -> int:
    modules_per_side = 17 + 4 * QR_VERSION
    return (modules_per_side + 2 * QR_BORDER_MODULES) * QR_MODULE_PX


def center_sample_half(cell_size_px: int) -> int:
    return max(1, cell_size_px // 8)

PAYLOAD_HEADER_REDUNDANCY = 3

HEADER_STRUCT = struct.Struct(">4sBBBBBHHHHHHI32sI")
PAYLOAD_HEADER_STRUCT = struct.Struct(">IHB")


@dataclass(frozen=True)
class PaperClipConfig:
    num_colors: int = 4
    cell_size_px: int = 28
    scan_dpi: int = 1200
    rs_redundancy: float = 0.20
    redundancy_pages: int = 0
    page_width_mm: float = 210.0
    page_height_mm: float = 297.0
    margin_mm: float = MARGIN_MM
    calibrated_colors: tuple[tuple[int, int, int], ...] = ()


def validate_config(config: PaperClipConfig) -> PaperClipConfig:
    if config.num_colors < 2:
        raise ValueError("num_colors must be at least 2")
    if config.cell_size_px < MIN_CELL_SIZE_PX:
        raise ValueError(f"cell_size_px must be at least {MIN_CELL_SIZE_PX}")
    if config.scan_dpi < 300:
        raise ValueError("scan_dpi must be at least 300")
    if config.rs_redundancy < 0.05 or config.rs_redundancy > 0.50:
        raise ValueError("rs_redundancy must be between 0.05 and 0.50")
    if config.redundancy_pages < 0:
        raise ValueError("redundancy_pages must be non-negative")
    if config.page_width_mm <= 0 or config.page_height_mm <= 0:
        raise ValueError("page dimensions must be positive")
    if config.margin_mm < 0:
        raise ValueError("margin_mm must be non-negative")
    return config


ALGO_FIELDS = ("num_colors", "cell_size_px", "scan_dpi", "rs_redundancy", "redundancy_pages", "calibrated_colors")


def save_config(config: PaperClipConfig, path: Path) -> None:
    data = {"paper_clip": {k: getattr(config, k) for k in ALGO_FIELDS}}
    path.write_bytes(tomli_w.dumps(data).encode())


def load_config(path: Path) -> PaperClipConfig:
    raw = tomllib.loads(path.read_text())
    section = raw.get("paper_clip", {})
    valid_fields = {f.name for f in __import__("dataclasses").fields(PaperClipConfig)}
    filtered = {k: v for k, v in section.items() if k in valid_fields}
    if "calibrated_colors" in filtered:
        filtered["calibrated_colors"] = tuple(
            tuple(c) for c in filtered["calibrated_colors"]
        )
    return validate_config(PaperClipConfig(**filtered))


def default_config() -> PaperClipConfig:
    return validate_config(PaperClipConfig())


def resolve_config(
    config_file: Path | None = None,
    num_colors: int | None = None,
    cell_size_px: int | None = None,
    paper_size: str | None = None,
) -> PaperClipConfig:
    from dataclasses import replace

    base = load_config(config_file) if config_file else default_config()
    overrides: dict[str, object] = {
        k: v
        for k, v in [
            ("num_colors", num_colors),
            ("cell_size_px", cell_size_px),
        ]
        if v is not None
    }
    if paper_size:
        from common.paper_sizes import config_with_page_dimensions
        base = config_with_page_dimensions(base, paper_size)
    return validate_config(replace(base, **overrides) if overrides else base)
