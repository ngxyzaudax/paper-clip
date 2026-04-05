import math
from functools import lru_cache

from common.types import RGB

CMYK = tuple[float, float, float, float]


def cmyk_to_rgb(c: float, m: float, y: float, k: float) -> RGB:
    r = round(255.0 * (1.0 - c) * (1.0 - k))
    g = round(255.0 * (1.0 - m) * (1.0 - k))
    b = round(255.0 * (1.0 - y) * (1.0 - k))
    return (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))


def _rgb_near(a: RGB, b: RGB, eps: float = 2.5) -> bool:
    return math.sqrt(sum((float(x) - float(y)) ** 2 for x, y in zip(a, b))) <= eps


def _append_unique(rgb: RGB, seen: list[RGB], out: list[RGB]) -> None:
    if any(_rgb_near(rgb, s) for s in seen):
        return
    seen.append(rgb)
    out.append(rgb)


def _ordered_cmyk_mixes() -> list[CMYK]:
    k_pair = 0.45
    k_triple = 0.35
    k_quad = 0.25
    return [
        (0.0, 0.0, 0.0, 1.0),
        (1.0, 0.0, 0.0, 0.0),
        (0.0, 1.0, 0.0, 0.0),
        (0.0, 0.0, 1.0, 0.0),
        (1.0, 1.0, 0.0, 0.0),
        (1.0, 0.0, 1.0, 0.0),
        (0.0, 1.0, 1.0, 0.0),
        (1.0, 0.0, 0.0, k_pair),
        (0.0, 1.0, 0.0, k_pair),
        (0.0, 0.0, 1.0, k_pair),
        (0.88, 0.88, 0.88, 0.0),
        (1.0, 1.0, 0.0, k_triple),
        (1.0, 0.0, 1.0, k_triple),
        (0.0, 1.0, 1.0, k_triple),
        (1.0, 1.0, 1.0, k_quad),
    ]


def _build_unique_print_rgb_sequence() -> list[RGB]:
    out: list[RGB] = []
    seen: list[RGB] = []
    for cmyk in _ordered_cmyk_mixes():
        _append_unique(cmyk_to_rgb(*cmyk), seen, out)
    return out


@lru_cache(maxsize=1)
def _print_rgb_sequence() -> tuple[RGB, ...]:
    return tuple(_build_unique_print_rgb_sequence())


def min_print_ink_colors() -> int:
    return 4


def max_print_ink_colors() -> int:
    return len(_print_rgb_sequence())


def ordered_print_palette(num_ink_colors: int) -> list[RGB]:
    if num_ink_colors < min_print_ink_colors():
        raise ValueError(
            f"num_ink_colors must be at least {min_print_ink_colors()} "
            "(CMYK primaries; blank paper is separate)",
        )
    seq = _print_rgb_sequence()
    if num_ink_colors > len(seq):
        raise ValueError(
            f"num_ink_colors cannot exceed {len(seq)} for distinct print-mixed colors",
        )
    return list(seq[:num_ink_colors])


def validate_print_ink_count(num_ink_colors: int) -> int:
    if num_ink_colors < min_print_ink_colors():
        raise ValueError(
            f"num_ink_colors must be at least {min_print_ink_colors()} "
            "(black, cyan, magenta, yellow; blank/white is symbol 0)",
        )
    if num_ink_colors > max_print_ink_colors():
        raise ValueError(f"num_ink_colors cannot exceed {max_print_ink_colors()}")
    return num_ink_colors


def min_print_symbols() -> int:
    return min_print_ink_colors() + 1


def max_print_symbols() -> int:
    return max_print_ink_colors() + 1


def validate_print_symbol_count(symbols: int) -> int:
    if symbols < 2:
        raise ValueError("alphabet size must be at least 2 symbols")
    validate_print_ink_count(symbols - 1)
    return symbols


def symbol_alphabet_options() -> list[tuple[str, int]]:
    return [
        (f"{n} symbols (0…{n - 1})", n)
        for n in range(min_print_symbols(), max_print_symbols() + 1)
    ]


def symbol_option_label(symbols: int) -> str:
    for label, n in symbol_alphabet_options():
        if n == symbols:
            return label
    return f"{symbols} symbols (0…{symbols - 1})"
