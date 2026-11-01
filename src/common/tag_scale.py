from common.format_spec import (
    FLAG_TAG_SCALE_MASK,
    FLAG_TAG_SCALE_SHIFT,
    TAG_SCALE_MM,
    TAG_SIZE_MM,
)


def tag_scale_index(tag_mm: float) -> int:
    nearest = min(range(len(TAG_SCALE_MM)), key=lambda index: abs(TAG_SCALE_MM[index] - tag_mm))
    if abs(TAG_SCALE_MM[nearest] - float(tag_mm)) > 0.05:
        raise ValueError(f"tag size {tag_mm:g} mm is not a supported AprilTag scale")
    return nearest


def tag_mm_from_flags(flags: int) -> float:
    index = (int(flags) >> FLAG_TAG_SCALE_SHIFT) & 0x7
    if index >= len(TAG_SCALE_MM):
        return TAG_SIZE_MM
    return TAG_SCALE_MM[index]


def flags_with_tag_mm(flags: int, tag_mm: float) -> int:
    index = tag_scale_index(tag_mm)
    cleared = int(flags) & ~FLAG_TAG_SCALE_MASK
    return cleared | (index << FLAG_TAG_SCALE_SHIFT)
