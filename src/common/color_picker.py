from common.cmyk_mix_tiers import CMYK
from common.scan_blend import print_rgb_sequence
from common.symbol_preset_labels import symbol_row_label
from common.types import RGB


def min_print_ink_colors() -> int:
    return 4


def max_print_ink_colors() -> int:
    return len(print_rgb_sequence())


def ordered_print_palette(num_ink_colors: int) -> list[RGB]:
    if num_ink_colors < min_print_ink_colors():
        raise ValueError(
            f"num_ink_colors must be at least {min_print_ink_colors()} "
            "(CMYK primaries; blank paper is separate)",
        )
    seq = print_rgb_sequence()
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
        (symbol_row_label(n), n)
        for n in range(min_print_symbols(), max_print_symbols() + 1)
    ]


def symbol_option_label(symbols: int) -> str:
    if symbols < min_print_symbols() or symbols > max_print_symbols():
        return f"{symbols} sym"
    return symbol_row_label(symbols)
