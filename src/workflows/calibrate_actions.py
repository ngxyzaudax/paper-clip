from calibration.print_sheet import print_calibration_sheet
from calibration.scan_record import all_reads, scan_record
from calibration.session_plan import view_label
from calibration.session_state import note_print, save_simulation
from calibration.sheet_io import calibration_dir, sheet_ready, write_sheet
from calibration.sheet_session import archive_session, next_scan_path, save_chosen, session_records
from calibration.sheet_sim import simulate_limits
from common.scan_capture import capture_page
from workflows.device_pick import dpi_to_use, saved_or_only_printer, scanner_to_use


def render_sheet() -> str:
    target = write_sheet()
    return f"Wrote {target / 'front.png'}, {target / 'back.png'}, and {target / 'layout.json'}."


def run_simulation() -> str:
    text = simulate_limits()
    save_simulation(text)
    return text


def printer_for_sheet() -> str:
    if not sheet_ready():
        raise ValueError("Render the sheet before printing.")
    return saved_or_only_printer()


def print_once(printer: str) -> str:
    folder = calibration_dir()
    job = print_calibration_sheet(printer, folder / "front.png", folder / "back.png")
    note_print(job.job_ids, job.sides)
    return f"Submitted job {', '.join(str(job_id) for job_id in job.job_ids)} ({job.sides}, {job.sheets} sheet)."


def scan_view() -> str:
    target = next_scan_path()
    scanner = scanner_to_use()
    chosen = dpi_to_use(scanner, None)
    capture_page(scanner, target, chosen)
    return f"Scanned {view_label(scan_record(target))} at {chosen} dpi."


def save_profile() -> str:
    chosen = save_chosen(all_reads(session_records()))
    return f"Saved the profile. One A4 side now holds {chosen.bytes_per_side:,} bytes."


def new_session() -> str:
    moved = archive_session()
    return f"Moved the previous scans to {moved}." if moved else "The session was already empty."
