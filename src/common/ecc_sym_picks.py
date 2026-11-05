ECC_SYM_PICKS: tuple[int, ...] = (
    10,
    20,
    30,
    40,
    50,
    60,
    80,
    100,
    128,
    160,
    200,
    254,
)


def closest_ecc_sym(count: int) -> int:
    return min(ECC_SYM_PICKS, key=lambda value: abs(value - count))


def ecc_sym_option_label(count: int) -> str:
    return f"{count} repair bytes"


def ecc_sym_pick_options() -> list[tuple[str, int]]:
    return [(ecc_sym_option_label(value), value) for value in ECC_SYM_PICKS]
