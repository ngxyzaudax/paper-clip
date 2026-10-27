from common.format_spec import TAG_QUIET_MM, TAG_SIZE_MM, TAG_TARGET_PITCH_MM
from common.geometry_measure import mm_to_px
from common.geometry_types import TagMark


def tag_pixel_size(dpi: int) -> int:
    raw = max(40, mm_to_px(TAG_SIZE_MM, dpi))
    snapped = max(40, (raw // 10) * 10)
    return snapped


def tag_quiet_px(dpi: int) -> int:
    return max(8, mm_to_px(TAG_QUIET_MM, dpi))


def choose_tag_grid(width: int, height: int, tag: int, quiet: int, dpi: int) -> tuple[int, int]:
    pitch = max(tag + 2 * quiet + mm_to_px(6.0, dpi), mm_to_px(TAG_TARGET_PITCH_MM, dpi))
    cols = max(2, min(5, max(1, width // pitch)))
    rows = max(2, min(6, max(1, height // pitch)))
    cols = _fit_count(cols, width, tag, quiet)
    rows = _fit_count(rows, height, tag, quiet)
    if _span(cols, tag, quiet) > width or _span(rows, tag, quiet) > height:
        raise ValueError("page is too small for the alignment tag grid")
    return rows, cols


def place_tags(
    width: int, height: int, top: int, tag: int, quiet: int, rows: int, cols: int,
) -> tuple[TagMark, ...]:
    xs = _centers(width, cols, tag, quiet)
    ys = _centers(height, rows, tag, quiet)
    marks: list[TagMark] = []
    for row, cy in enumerate(ys):
        for col, cx in enumerate(xs):
            marks.append(TagMark(
                tag_id=row * cols + col,
                row=row,
                col=col,
                x=int(round(cx - tag / 2)),
                y=int(round(top + cy - tag / 2)),
                size=tag,
            ))
    return tuple(marks)


def _fit_count(count: int, length: int, tag: int, quiet: int) -> int:
    while count > 2 and _span(count, tag, quiet) > length:
        count -= 1
    return count


def _span(count: int, tag: int, quiet: int) -> int:
    return count * tag + (count + 1) * quiet


def _centers(length: int, count: int, tag: int, quiet: int) -> list[float]:
    inset = tag / 2 + quiet
    if count <= 1:
        return [length / 2]
    span = max(0.0, length - 2 * inset)
    return [inset + span * index / (count - 1) for index in range(count)]
