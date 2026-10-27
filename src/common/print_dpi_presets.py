POPULAR_PRINT_DPIS: tuple[int, ...] = (300, 360, 600, 720, 1200, 1440, 2400)


def closest_popular_print_dpi(dpi: int) -> int:
    if dpi in POPULAR_PRINT_DPIS:
        return dpi
    return min(POPULAR_PRINT_DPIS, key=lambda s: abs(s - dpi))


def print_dpi_select_options() -> list[tuple[str, int]]:
    return [(f"{d} dpi", d) for d in POPULAR_PRINT_DPIS]


def print_dpi_option_label(dpi: int) -> str:
    for label, d in print_dpi_select_options():
        if d == dpi:
            return label
    return f"{dpi} dpi"
