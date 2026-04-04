import math

from common.config import DOT_GAIN_FACTOR, PaperClipConfig
from common.types import RGB


def dot_fill_fraction(cell_size: int) -> float:
    _ = cell_size
    return 1.0 / DOT_GAIN_FACTOR


def _hsl_to_rgb(h: float, s: float, l: float) -> RGB:
    c = (1 - abs(2 * l - 1)) * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = l - c / 2
    if h < 60:
        r, g, b = c, x, 0.0
    elif h < 120:
        r, g, b = x, c, 0.0
    elif h < 180:
        r, g, b = 0.0, c, x
    elif h < 240:
        r, g, b = 0.0, x, c
    elif h < 300:
        r, g, b = x, 0.0, c
    else:
        r, g, b = c, 0.0, x
    return (int((r + m) * 255), int((g + m) * 255), int((b + m) * 255))


def _rgb_distance(a: RGB, b: RGB) -> float:
    return math.sqrt(sum((c1 - c2) ** 2 for c1, c2 in zip(a, b)))


def _brightness(rgb: RGB) -> float:
    return 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]


BLANK_RGB: RGB = (255, 255, 255)
MIN_BLANK_BRIGHTNESS = 220.0
MIN_BLANK_RGB_DISTANCE = 60.0


def _is_too_close_to_blank(rgb: RGB) -> bool:
    return _brightness(rgb) > MIN_BLANK_BRIGHTNESS and _rgb_distance(rgb, BLANK_RGB) < MIN_BLANK_RGB_DISTANCE


def _hue_based_palette(num_colors: int) -> list[RGB]:
    return [_hsl_to_rgb((i / num_colors) * 360.0, 1.0, 0.5) for i in range(num_colors)]


def _maximize_rgb_separation(candidates: list[RGB], num_colors: int) -> list[RGB]:
    selected = [0]
    remaining = set(range(1, len(candidates)))
    while len(selected) < num_colors and remaining:
        best_idx = -1
        best_min_dist = -1.0
        for idx in remaining:
            min_dist_selected = min(_rgb_distance(candidates[idx], candidates[s]) for s in selected)
            dist_to_blank = _rgb_distance(candidates[idx], BLANK_RGB)
            min_dist = min(min_dist_selected, dist_to_blank)
            if min_dist > best_min_dist:
                best_min_dist = min_dist
                best_idx = idx
        selected.append(best_idx)
        remaining.discard(best_idx)
    return [candidates[i] for i in selected]


def generate_palette(num_colors: int) -> list[RGB]:
    candidates = [(0, 0, 0)] + _hue_based_palette(max(num_colors * 4, 36))
    candidates = [c for c in candidates if not _is_too_close_to_blank(c)]
    return _maximize_rgb_separation(candidates, num_colors)


def palette_from_config(config: PaperClipConfig) -> list[RGB]:
    return generate_palette(config.num_colors)
