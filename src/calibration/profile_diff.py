from calibration.profile import DensityProfile, load_density_profile
from calibration.sheet_limits import ChosenProfile
from common.config import resolve_config
from common.page_capacity import data_capacity_bytes

_FIELDS = (
    ("Cell", "cell_size_px", "{:g} px"),
    ("Symbols", "num_symbols", "{:g}"),
    ("AprilTag", "tag_size_mm", "{:g} mm"),
    ("Tag pitch", "tag_pitch_mm", "{:g} mm"),
    ("QR module", "qr_module_mm", "{:g} mm"),
    ("Dot ratio", "dot_ratio", "{:g}"),
)


def profile_rows(chosen: ChosenProfile) -> list[tuple[str, str, str]]:
    """Rows of setting, value now, and value after saving, for a confirmation view."""
    current = load_density_profile()
    rows = [
        (label, _value(current, key, pattern), pattern.format(getattr(chosen, key)))
        for label, key, pattern in _FIELDS
    ]
    rows.append(("A4 bytes per side", _bytes_now(current), f"{chosen.bytes_per_side:,}"))
    return rows


def format_profile_rows(rows: list[tuple[str, str, str]]) -> str:
    lines = [f"{'Setting':<18} {'Now':<12} After save"]
    lines += [f"{label:<18} {now:<12} {after}" for label, now, after in rows]
    return "\n".join(lines)


def _value(current: DensityProfile | None, key: str, pattern: str) -> str:
    if current is None:
        return "default"
    return pattern.format(getattr(current, key))


def _bytes_now(current: DensityProfile | None) -> str:
    if current is None:
        return f"{data_capacity_bytes(resolve_config()):,}"
    config = resolve_config(
        cell_size_px=current.cell_size_px,
        num_symbols=current.num_symbols,
        tag_size_mm=current.tag_size_mm,
        tag_pitch_mm=current.tag_pitch_mm,
        qr_module_mm=current.qr_module_mm,
        dot_ratio=current.dot_ratio,
        print_dpi=current.print_dpi,
    )
    return f"{data_capacity_bytes(config):,}"
