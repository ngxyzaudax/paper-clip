from pathlib import Path

import typer

from calibration.profile_diff import format_profile_rows, profile_rows
from calibration.session_plan import next_instruction, view_label
from calibration.session_state import note_print, save_simulation
from calibration.session_view import format_steps, session_view
from calibration.sheet_io import calibration_dir, write_sheet
from calibration.sheet_limits import choose_profile
from calibration.sheet_report import format_limits
from calibration.sheet_session import archive_session, next_scan_path, save_chosen, score_paths, session_records
from calibration.sheet_sim import simulate_limits
from calibration.scan_record import scan_record
from cli.calibrate_output import confirm_or_exit, require_clean, require_sheet, show_limits
from cli.calibrate_scan import dpi_to_use, scanner_to_use
from cli.display import print_error, print_success
from cli.print_cmd import _saved_or_only_printer
from common.device_error import DeviceError
from common.scan_capture import capture_page

calibrate_app = typer.Typer(help="Measure QR, AprilTag, dot, and symbol limits on one duplex A4 sheet.")
_SESSION_HELP = "A scan or a directory. Default: data/calibration/session"


@calibrate_app.command("status")
def status_command() -> None:
    """Show the calibration steps, the next instruction, and the limits measured so far."""
    view = session_view()
    typer.echo(format_steps(view.steps))
    typer.echo(f"\nNext: {view.next_step}\n")
    typer.echo("\n".join(view.scans) or "No scans in this session.")
    if view.chosen is not None:
        typer.echo("\n" + format_limits(view.axes, view.chosen))


@calibrate_app.command("sheet")
def sheet_command(
    output: Path = typer.Option(None, "--output", help="Directory for front.png, back.png, and layout.json"),
) -> None:
    """Render the duplex calibration sheet and check the clean pages."""
    destination = write_sheet(output)
    require_clean(score_paths([destination / "front.png", destination / "back.png"]))
    print_success(f"Wrote {destination / 'front.png'} and {destination / 'back.png'}. The digital check passed.")


@calibrate_app.command("simulate")
def simulate_command() -> None:
    """Run the ink model at strengths 0.3, 0.6, and 1.0. Does not print or save a profile."""
    text = simulate_limits()
    save_simulation(text)
    typer.echo(text)


@calibrate_app.command("print")
def print_command(
    yes: bool = typer.Option(False, "--yes", help="Send the one job without asking"),
    printer_uri: str | None = typer.Option(None, "--uri", help="IPP printer URI"),
) -> None:
    """Send one duplex job. A rejection is reported and not retried."""
    from calibration.print_sheet import print_calibration_sheet

    folder = require_sheet()
    try:
        printer = printer_uri or _saved_or_only_printer()
        confirm_or_exit(yes, f"Send one duplex calibration job to {printer}?")
        job = print_calibration_sheet(printer, folder / "front.png", folder / "back.png", typer.echo)
    except DeviceError as exc:
        print_error(str(exc))
        raise typer.Exit(1) from exc
    note_print(job.job_ids, job.sides)
    print_success(f"Submitted job {', '.join(map(str, job.job_ids))} ({job.sides}, {job.sheets} sheet).")
    typer.echo(f"Next: {next_instruction(session_records())}")


@calibrate_app.command("scan")
def scan_command(
    scanner_uri: str | None = typer.Option(None, "--uri", help="eSCL scanner URI"),
    dpi: int | None = typer.Option(None, "--dpi", help="Scan resolution"),
    now: bool = typer.Option(False, "--now", help="Scan without waiting for Enter"),
) -> None:
    """Scan one view of the sheet, read it, and say which view to scan next."""
    typer.echo(next_instruction(session_records()))
    if not now:
        typer.prompt("Press Enter when the sheet is on the glass", default="", show_default=False)
    target = next_scan_path()
    try:
        scanner = scanner_to_use(scanner_uri)
        chosen = dpi_to_use(scanner, dpi)
        typer.echo(f"Scanning {target.name} at {chosen} dpi.")
        capture_page(scanner, target, chosen)
    except DeviceError as exc:
        print_error(str(exc))
        raise typer.Exit(1) from exc
    print_success(f"{view_label(scan_record(target))} at {chosen} dpi.")
    typer.echo(f"Next: {session_view().next_step}")


@calibrate_app.command("score")
def score_command(scans: Path = typer.Argument(None, help=_SESSION_HELP)) -> None:
    """Score scans and print the per-aspect table. Does not save the profile."""
    show_limits(score_paths([scans or (calibration_dir() / "session")]))


@calibrate_app.command("save")
def save_command(
    scans: Path = typer.Argument(None, help=_SESSION_HELP),
    yes: bool = typer.Option(False, "--yes", help="Save without asking"),
) -> None:
    """Save the profile with one step of margin on each axis."""
    reads = score_paths([scans or (calibration_dir() / "session")])
    show_limits(reads)
    typer.echo(format_profile_rows(profile_rows(choose_profile(reads))))
    confirm_or_exit(yes, "Save this profile?")
    chosen = save_chosen(reads)
    print_success(f"Saved the profile. One A4 side holds {chosen.bytes_per_side:,} bytes.")


@calibrate_app.command("new")
def new_command(yes: bool = typer.Option(False, "--yes", help="Archive without asking")) -> None:
    """Move the current session scans to the archive and start fresh."""
    confirm_or_exit(yes, "Move the current session scans to data/calibration/archive?")
    moved = archive_session()
    print_success(f"Archived to {moved}" if moved else "The session was already empty.")
