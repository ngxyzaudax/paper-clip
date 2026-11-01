from typing import NamedTuple

from calibration.profile import load_density_profile
from calibration.scan_record import ScanRecord, all_reads
from calibration.session_plan import SIDES, VIEWS_PER_SIDE, coverage, next_instruction, view_label
from calibration.session_state import print_note, simulation_text
from calibration.sheet_io import sheet_ready
from calibration.sheet_limits import AxisLimit, ChosenProfile, axis_limits, choose_profile
from calibration.sheet_session import session_records

_PROFILE_KEYS = ("cell_size_px", "num_symbols", "tag_size_mm", "tag_pitch_mm", "qr_module_mm", "dot_ratio")


class SessionView(NamedTuple):
    steps: tuple[tuple[bool, str], ...]
    next_step: str
    scans: tuple[str, ...]
    axes: tuple[AxisLimit, ...]
    chosen: ChosenProfile | None


def session_view() -> SessionView:
    """Everything the calibration screens show, derived from the files under data/calibration."""
    records = session_records()
    reads = all_reads(records)
    chosen = choose_profile(reads) if reads else None
    return SessionView(
        _steps(records, chosen),
        _next_step(records, chosen),
        tuple(view_label(record) for record in records),
        axis_limits(reads) if reads else (),
        chosen,
    )


def format_steps(steps: tuple[tuple[bool, str], ...]) -> str:
    return "\n".join(f"{'[x]' if done else '[ ]'} {index}. {text}" for index, (done, text) in enumerate(steps, 1))


def _steps(records: tuple[ScanRecord, ...], chosen: ChosenProfile | None) -> tuple[tuple[bool, str], ...]:
    note = print_note()
    seen = coverage(records)
    return (
        (sheet_ready(), "Render the sheet"),
        (simulation_text() is not None, "Simulate ink damage (optional)"),
        (note is not None, f"Print one duplex sheet ({note})" if note else "Print one duplex sheet"),
        (seen.complete, f"Scan both sides ({seen.views} of {VIEWS_PER_SIDE * len(SIDES)})"),
        (_saved(chosen), "Save the profile"),
    )


def _next_step(records: tuple[ScanRecord, ...], chosen: ChosenProfile | None) -> str:
    if not sheet_ready():
        return "Render the sheet."
    if not records and print_note() is None:
        return "Print the sheet, then scan it. Printing is one duplex job with no retries."
    if coverage(records).complete and not _saved(chosen):
        return "Both sides are in. Review the table and save the profile."
    return next_instruction(records)


def _saved(chosen: ChosenProfile | None) -> bool:
    saved = load_density_profile()
    if chosen is None or saved is None:
        return False
    return all(abs(float(getattr(saved, key)) - float(getattr(chosen, key))) < 1e-6 for key in _PROFILE_KEYS)
