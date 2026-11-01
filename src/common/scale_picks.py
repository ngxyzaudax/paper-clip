from common.format_spec import DOT_RATIO_SCALE, QR_SCALE_MM, TAG_SCALE_MM

TAG_PITCH_PICKS_MM: tuple[float, ...] = (16.0, 24.0, 32.0)


def qr_module_options() -> list[tuple[str, float]]:
    return [(f"{mm:g} mm", mm) for mm in QR_SCALE_MM]


def dot_ratio_options() -> list[tuple[str, float]]:
    return [(f"{ratio:g}", ratio) for ratio in DOT_RATIO_SCALE]


def tag_size_options() -> list[tuple[str, float]]:
    return [(f"{mm:g} mm", mm) for mm in TAG_SCALE_MM]


def tag_pitch_options() -> list[tuple[str, float]]:
    return [(f"{mm:g} mm", mm) for mm in TAG_PITCH_PICKS_MM]


def qr_module_label(module_mm: float) -> str:
    return f"{module_mm:g} mm"


def dot_ratio_label(ratio: float) -> str:
    return f"{ratio:g}"


def millimetre_label(value_mm: float) -> str:
    return f"{value_mm:g} mm"
