from common.types import RGB

CMYK = tuple[float, float, float, float]

K_PAIR = 0.45
K_TRIPLE = 0.35
K_QUAD = 0.25


def cmyk_to_rgb(c: float, m: float, y: float, k: float) -> RGB:
    r = round(255.0 * (1.0 - c) * (1.0 - k))
    g = round(255.0 * (1.0 - m) * (1.0 - k))
    b = round(255.0 * (1.0 - y) * (1.0 - k))
    return (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))


def primary_inks() -> list[CMYK]:
    return [
        (0.0, 0.0, 0.0, 1.0),
        (1.0, 0.0, 0.0, 0.0),
        (0.0, 1.0, 0.0, 0.0),
        (0.0, 0.0, 1.0, 0.0),
    ]


def two_ink_full_mixes() -> list[CMYK]:
    return [
        (1.0, 1.0, 0.0, 0.0),
        (1.0, 0.0, 1.0, 0.0),
        (0.0, 1.0, 1.0, 0.0),
    ]


def two_ink_with_black_tints() -> list[CMYK]:
    return [
        (1.0, 0.0, 0.0, K_PAIR),
        (0.0, 1.0, 0.0, K_PAIR),
        (0.0, 0.0, 1.0, K_PAIR),
    ]


def neutral_gray() -> list[CMYK]:
    return [(0.88, 0.88, 0.88, 0.0)]


def three_ink_mixes() -> list[CMYK]:
    return [
        (1.0, 1.0, 0.0, K_TRIPLE),
        (1.0, 0.0, 1.0, K_TRIPLE),
        (0.0, 1.0, 1.0, K_TRIPLE),
    ]


def four_ink_mix() -> list[CMYK]:
    return [(1.0, 1.0, 1.0, K_QUAD)]


def ordered_tier_groups() -> list[tuple[str, list[CMYK]]]:
    return [
        ("primaries (K, C, M, Y)", primary_inks()),
        ("2-ink secondaries", two_ink_full_mixes()),
        ("2-ink + K tints", two_ink_with_black_tints()),
        ("neutral gray", neutral_gray()),
        ("3-ink mixes", three_ink_mixes()),
        ("4-ink mix", four_ink_mix()),
    ]
