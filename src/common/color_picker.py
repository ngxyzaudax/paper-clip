from common.scan_blend import print_rgb_sequence
from common.symbol_count_picks import (
    allowed_print_symbol_counts,
)
from common.symbol_preset_labels import symbol_row_label
from common.types import RGB

_PRINTABLE_SYMS: tuple[int, ...] = allowed_print_symbol_counts()
_MIN_INK = 4
_MAX_INK = 10


def min_print_ink_colors() -> int:
    return _MIN_INK


def max_print_ink_colors() -> int:
    return _MAX_INK



def ordered_print_palette(num_ink_colors: int) -> list[RGB]:
    if num_ink_colors < min_print_ink_colors() or num_ink_colors > max_print_ink_colors():
        a, b, c = _MIN_INK, 7, _MAX_INK
        raise ValueError(
            f"num_ink_colors must be {a} (CMYK+blank), {b} (CMYK+RGB+blank), or {c} (add K-tints+blank), "
            f"got {num_ink_colors}",
        )
    seq = print_rgb_sequence()
    if num_ink_colors > len(seq):
        raise ValueError(
            f"num_ink_colors cannot exceed {len(seq)} for distinct print-mixed colors",
        )
    return list(seq[:num_ink_colors])


def validate_print_ink_count(num_ink_colors: int) -> int:
    if num_ink_colors not in (_MIN_INK, 7, _MAX_INK):
        a, b, c = _MIN_INK, 7, _MAX_INK
        raise ValueError(
            f"num_ink_colors must be {a} (CMYK+blank), {b} (CMYK+RGB+blank), or {c} (add K-tints+blank), "
            f"got {num_ink_colors}",
        )
    n = len(print_rgb_sequence())
    if num_ink_colors > n:
        raise ValueError(f"num_ink_colors cannot exceed {n}")
    return num_ink_colors


def validate_print_symbol_count(symbols: int) -> int:
    if symbols not in _PRINTABLE_SYMS:
        a, b, c = _PRINTABLE_SYMS
        raise ValueError(
            f"alphabet size must be {a} (CMYK+blank), {b} (CMYK+RGB+blank), or {c} (add K-tints+blank), "
            f"got {symbols}",
        )
    validate_print_ink_count(symbols - 1)
    return symbols


def symbol_alphabet_options() -> list[tuple[str, int]]:
    return [(symbol_row_label(n), n) for n in _PRINTABLE_SYMS]


def symbol_option_label(symbols: int) -> str:
    if symbols not in _PRINTABLE_SYMS:
        return f"{symbols} sym"
    return symbol_row_label(symbols)
