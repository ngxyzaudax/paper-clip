CELL_SIZE_PICK_MIN = 5
CELL_SIZE_PICK_MAX = 25


def cell_size_pick_options() -> list[tuple[str, int]]:
    return [(f"{n} px", n) for n in range(CELL_SIZE_PICK_MIN, CELL_SIZE_PICK_MAX + 1)]


def clamp_cell_size_pick(px: int) -> int:
    return max(CELL_SIZE_PICK_MIN, min(CELL_SIZE_PICK_MAX, px))


def cell_size_pick_label(px: int) -> str:
    for label, n in cell_size_pick_options():
        if n == px:
            return label
    return f"{px} px"
