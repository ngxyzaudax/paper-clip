_PRINTABLE_SYMS: tuple[int, ...] = (5, 8, 11)


def allowed_print_symbol_counts() -> tuple[int, ...]:
    return _PRINTABLE_SYMS


def clamp_print_symbol_count(n: int) -> int:
    return min(_PRINTABLE_SYMS, key=lambda a: (abs(a - n), a))
