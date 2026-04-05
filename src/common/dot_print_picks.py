from common.config import MAX_DOT_GAIN_FACTOR, MIN_DOT_GAIN_FACTOR

DOT_GAIN_PICKS: tuple[float, ...] = (
    1.05,
    1.2,
    1.35,
    1.5,
    1.65,
    1.8,
    2.0,
    2.2,
    2.4,
    2.6,
    2.8,
    3.0,
)

DOT_GUARD_PICKS: tuple[int, ...] = tuple(range(0, 13))


def dot_gain_pick_options() -> list[tuple[str, float]]:
    return [(f"{x:.2f} gain", x) for x in DOT_GAIN_PICKS]


def dot_guard_pick_options() -> list[tuple[str, int]]:
    return [(f"{n} px guard", n) for n in DOT_GUARD_PICKS]


def closest_dot_gain(x: float) -> float:
    x = max(MIN_DOT_GAIN_FACTOR, min(MAX_DOT_GAIN_FACTOR, x))
    return min(DOT_GAIN_PICKS, key=lambda v: abs(v - x))


def closest_dot_guard(px: int) -> int:
    px = max(0, min(DOT_GUARD_PICKS[-1], px))
    return min(DOT_GUARD_PICKS, key=lambda v: abs(v - px))


def dot_gain_pick_label(gain: float) -> str:
    for label, v in dot_gain_pick_options():
        if abs(v - gain) < 1e-6:
            return label
    return f"{gain:.2f} gain"


def dot_guard_pick_label(px: int) -> str:
    for label, v in dot_guard_pick_options():
        if v == px:
            return label
    return f"{px} px guard"
