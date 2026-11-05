from typing import NamedTuple

from common.config import PaperClipConfig
from common.device_config import get_printer_settings, load_device_config, save_device_config

_KEYS = (
    "cell_size_px",
    "num_symbols",
    "tag_size_mm",
    "tag_pitch_mm",
    "print_dpi",
    "bits_per_cm2",
    "qr_module_mm",
    "dot_ratio",
)


class DensityProfile(NamedTuple):
    cell_size_px: int
    num_symbols: int
    tag_size_mm: float
    tag_pitch_mm: float
    print_dpi: int
    bits_per_cm2: float
    qr_module_mm: float
    dot_ratio: float


def load_density_profile() -> DensityProfile | None:
    raw = get_printer_settings().get("profile") or {}
    if any(key not in raw for key in _KEYS):
        return None
    try:
        return _parse(raw)
    except (TypeError, ValueError):
        return None


def profile_density(config: PaperClipConfig) -> float:
    area = config.page_width_mm * config.page_height_mm / 100.0
    if area <= 0:
        return 0.0
    from common.page_capacity import data_capacity_bytes
    return data_capacity_bytes(config) * 8 / area


def save_density_profile(config: PaperClipConfig, bits_per_cm2: float) -> None:
    current = load_device_config()
    profile = dict(current["printer"].get("profile") or {})
    profile.update({
        "cell_size_px": str(config.cell_size_px),
        "num_symbols": str(config.num_symbols),
        "tag_size_mm": f"{config.tag_size_mm:g}",
        "tag_pitch_mm": f"{config.tag_pitch_mm:g}",
        "print_dpi": str(config.print_dpi),
        "bits_per_cm2": f"{bits_per_cm2:.2f}",
        "qr_module_mm": f"{config.qr_module_mm:g}",
        "dot_ratio": f"{config.dot_ratio:g}",
    })
    current["printer"]["profile"] = profile
    save_device_config(current)


def _parse(raw: dict[str, str]) -> DensityProfile:
    return DensityProfile(
        cell_size_px=int(raw["cell_size_px"]),
        num_symbols=int(raw["num_symbols"]),
        tag_size_mm=float(raw["tag_size_mm"]),
        tag_pitch_mm=float(raw["tag_pitch_mm"]),
        print_dpi=int(raw["print_dpi"]),
        bits_per_cm2=float(raw["bits_per_cm2"]),
        qr_module_mm=float(raw["qr_module_mm"]),
        dot_ratio=float(raw["dot_ratio"]),
    )
