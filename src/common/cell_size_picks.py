CELL_SIZE_PICK_VALUES: tuple[int, ...] = (24, 32, 40, 48, 64)
CELL_SIZE_PICK_MIN = CELL_SIZE_PICK_VALUES[0]
CELL_SIZE_PICK_MAX = CELL_SIZE_PICK_VALUES[-1]


def _nearest_cell_size_pick(bounded: int) -> int:
    return min(CELL_SIZE_PICK_VALUES, key=lambda n: (abs(n - bounded), n))


def cell_size_pick_options() -> list[tuple[str, int]]:
    return [(f"{n} px", n) for n in CELL_SIZE_PICK_VALUES]


def validate_cell_size_pick(px: int) -> int:
    if px not in CELL_SIZE_PICK_VALUES:
        allowed = ", ".join(str(n) for n in CELL_SIZE_PICK_VALUES)
        raise ValueError(f"cell_size_px must be one of: {allowed}; got {px}")
    return px


def clamp_cell_size_pick(px: int) -> int:
    bounded = max(CELL_SIZE_PICK_MIN, min(CELL_SIZE_PICK_MAX, px))
    return _nearest_cell_size_pick(bounded)


def cell_size_pick_label(px: int) -> str:
    for label, n in cell_size_pick_options():
        if n == px:
            return label
    return f"{px} px"
