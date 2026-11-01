from common.format_spec import (
    CELL_FIELD_MASK,
    DOT_DIAMETER_RATIO,
    DOT_RATIO_SCALE,
    DOT_RATIO_SHIFT,
)


def dot_ratio_index(ratio: float) -> int:
    nearest = min(range(len(DOT_RATIO_SCALE)), key=lambda index: abs(DOT_RATIO_SCALE[index] - ratio))
    if abs(DOT_RATIO_SCALE[nearest] - float(ratio)) > 0.01:
        raise ValueError(f"dot ratio {ratio:g} is not a supported scale")
    return nearest


def pack_cell_field(cell_px: int, ratio: float) -> int:
    if cell_px < 0 or cell_px > CELL_FIELD_MASK:
        raise ValueError(f"cell_size_px {cell_px} does not fit in the header field")
    return int(cell_px) | (dot_ratio_index(ratio) << DOT_RATIO_SHIFT)


def unpack_cell_field(field: int) -> tuple[int, float]:
    cell = int(field) & CELL_FIELD_MASK
    index = (int(field) >> DOT_RATIO_SHIFT) & 0xF
    if index >= len(DOT_RATIO_SCALE):
        return cell, DOT_DIAMETER_RATIO
    return cell, DOT_RATIO_SCALE[index]
