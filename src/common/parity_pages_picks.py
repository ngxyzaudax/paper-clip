PARITY_PAGES_PICKS: tuple[int, ...] = tuple(range(0, 11))


def closest_parity_pages(n: int) -> int:
    n = max(0, min(PARITY_PAGES_PICKS[-1], n))
    return min(PARITY_PAGES_PICKS, key=lambda v: abs(v - n))


def parity_pages_pick_options() -> list[tuple[str, int]]:
    return [(f"{k} parity page{'s' if k != 1 else ''}", k) for k in PARITY_PAGES_PICKS]


def parity_pages_option_label(n: int) -> str:
    for label, v in parity_pages_pick_options():
        if v == n:
            return label
    return f"{n} parity pages"
