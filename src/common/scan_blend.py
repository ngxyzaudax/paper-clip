import math
from functools import lru_cache

import numpy as np

from common.cmyk_mix_tiers import cmyk_to_rgb, ordered_tier_groups
from common.config import PaperClipConfig
from common.types import RGB

MIN_DELTA_E = 8.0
_XN, _YN, _ZN = 0.95047, 1.0, 1.08883


def _srgb_channel_to_linear(u: float) -> float:
    if u <= 0.04045:
        return u / 12.92
    return ((u + 0.055) / 1.055) ** 2.4


def rgb_to_lab(rgb: RGB) -> np.ndarray:
    r, g, b = (x / 255.0 for x in rgb)
    rl = _srgb_channel_to_linear(r)
    gl = _srgb_channel_to_linear(g)
    bl = _srgb_channel_to_linear(b)
    x = rl * 0.4124564 + gl * 0.3575761 + bl * 0.1804375
    y = rl * 0.2126729 + gl * 0.7151522 + bl * 0.0721750
    z = rl * 0.0193339 + gl * 0.1191920 + bl * 0.9503041

    def f(t: float) -> float:
        if t > 0.008856:
            return t ** (1.0 / 3.0)
        return (7.787 * t) + (16.0 / 116.0)

    fx, fy, fz = f(x / _XN), f(y / _YN), f(z / _ZN)
    L = 116.0 * fy - 16.0
    a = 500.0 * (fx - fy)
    b2 = 200.0 * (fy - fz)
    return np.array([L, a, b2], dtype=np.float64)


def delta_e_76(lab_a: np.ndarray, lab_b: np.ndarray) -> float:
    d = lab_a - lab_b
    return float(np.sqrt(np.dot(d, d)))


def dot_area_coverage_ratio(
    cell_size_px: int,
) -> float:
    radius = max(1, int(cell_size_px / 2))
    dot_area = math.pi * float(radius) ** 2
    cell_area = float(cell_size_px) ** 2
    return min(1.0, dot_area / cell_area)


def expected_scan_rgb(ink_rgb: RGB, coverage: float) -> RGB:
    w = coverage
    out = []
    for ch in ink_rgb:
        v = (1.0 - w) * 255.0 + w * float(ch)
        out.append(max(0, min(255, round(v))))
    return (out[0], out[1], out[2])


def build_distinct_print_sequence(
    min_delta_e: float = MIN_DELTA_E,
) -> tuple[tuple[RGB, ...], tuple[tuple[str, int], ...]]:
    cfg = PaperClipConfig()
    coverage = dot_area_coverage_ratio(
        cfg.cell_size_px,
    )
    groups = ordered_tier_groups()
    accepted_rgb: list[RGB] = []
    accepted_labs: list[np.ndarray] = []
    tier_cumulative: list[tuple[str, int]] = []
    running = 0
    for tier_name, cmyks in groups:
        tier_start = running
        for cmyk in cmyks:
            ink = cmyk_to_rgb(*cmyk)
            sample = expected_scan_rgb(ink, coverage)
            lab = rgb_to_lab(sample)
            if any(delta_e_76(lab, prev) < min_delta_e for prev in accepted_labs):
                continue
            accepted_labs.append(lab)
            accepted_rgb.append(ink)
            running += 1
        if running > tier_start:
            tier_cumulative.append((tier_name, running))
    return tuple(accepted_rgb), tuple(tier_cumulative)


@lru_cache(maxsize=1)
def cached_print_sequence() -> tuple[tuple[RGB, ...], tuple[tuple[str, int], ...]]:
    return build_distinct_print_sequence()


def print_rgb_sequence() -> tuple[RGB, ...]:
    return cached_print_sequence()[0]


def tier_cumulative_ends() -> tuple[tuple[str, int], ...]:
    return cached_print_sequence()[1]
