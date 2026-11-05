from common.types import SymbolGrid

STRIPE = -2


def mark_unused(grid: SymbolGrid, valid_order: list[tuple[int, int]]) -> SymbolGrid:
    for row, col in valid_order:
        if grid[row][col] < 0:
            grid[row][col] = STRIPE
    return grid
