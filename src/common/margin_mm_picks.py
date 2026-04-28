MARGIN_MM_PICKS: tuple[float, ...] = tuple(round(i * 0.5, 1) for i in range(11))


def closest_margin_mm(mm: float) -> float:
    mm = max(MARGIN_MM_PICKS[0], min(MARGIN_MM_PICKS[-1], mm))
    return min(MARGIN_MM_PICKS, key=lambda v: abs(v - mm))


def margin_mm_pick_options() -> list[tuple[str, float]]:
    return [(f"{v:g} mm (all sides)", v) for v in MARGIN_MM_PICKS]


def margin_mm_option_label(mm: float) -> str:
    for label, v in margin_mm_pick_options():
        if abs(v - mm) < 1e-6:
            return label
    return f"{mm:g} mm (all sides)"
