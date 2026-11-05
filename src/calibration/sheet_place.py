from calibration.sheet_fill import back_patches, front_patches
from calibration.sheet_spec import FRAME_TAG_MM, PAGE_H_MM, PAGE_W_MM, FrameTag, SheetSide


def sheet_side(name: str) -> SheetSide:
    patches = back_patches() if name == "back" else front_patches()
    return SheetSide(name, _frame(name), patches)


def _frame(side: str) -> tuple[FrameTag, ...]:
    base = 500 if side == "front" else 520
    points = [(x, 9.0) for x in (9.0, 60.0, 111.0, 162.0, 201.0)]
    points += [(x, PAGE_H_MM - 9.0) for x in (9.0, 60.0, 111.0, 162.0, 201.0)]
    points += [(9.0, y) for y in (80.0, 151.0, 222.0)]
    points += [(PAGE_W_MM - 9.0, y) for y in (80.0, 151.0, 222.0)]
    if any(abs(x) < FRAME_TAG_MM for x, _y in points):
        raise ValueError("frame tag leaves the page")
    return tuple(FrameTag(base + index, x, y) for index, (x, y) in enumerate(points))
