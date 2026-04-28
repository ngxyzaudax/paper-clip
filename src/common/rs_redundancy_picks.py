RS_REDUNDANCY_PICKS: tuple[float, ...] = (
    0.05,
    0.10,
    0.15,
    0.20,
    0.25,
    0.30,
    0.35,
    0.40,
    0.45,
    0.50,
)


def closest_rs_redundancy(r: float) -> float:
    return min(RS_REDUNDANCY_PICKS, key=lambda v: abs(v - r))


def rs_redundancy_pick_options() -> list[tuple[str, float]]:
    return [(f"{int(v * 100)}% RS redundancy", v) for v in RS_REDUNDANCY_PICKS]


def rs_redundancy_option_label(r: float) -> str:
    for label, v in rs_redundancy_pick_options():
        if abs(v - r) < 1e-6:
            return label
    return f"{r:.0%} RS redundancy"
