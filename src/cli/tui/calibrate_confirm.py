from collections.abc import Callable
from typing import Protocol

from textual.app import App

from calibration.session_plan import SIDES, VIEWS_PER_SIDE, coverage
from calibration.sheet_session import session_records
from cli.tui.calibrate_flow import new_session, print_once, printer_for_sheet, save_preview, save_profile
from cli.tui.confirm_screen import ConfirmScreen

_PRINT_BODY = (
    "Printer: {printer}\n\n"
    "Sends ONE duplex A4 job with front.png and back.png. "
    "If the printer cannot print both sides in one job, it sends two one-sided jobs instead. "
    "Nothing is retried; if the job fails, check the printer before pressing Print again."
)
_NEEDED = VIEWS_PER_SIDE * len(SIDES)
_INCOMPLETE = "\n\nOnly {views} of {needed} sides are scanned. Limits from one side are less certain."


class CalibrationPanel(Protocol):
    app: App

    def run_action(self, action: Callable[[], str], pending: str) -> None: ...

    def call_in_worker(self, action: Callable[[], object], then: Callable[[object], None], pending: str) -> None: ...


def confirm_print(panel: CalibrationPanel) -> None:
    panel.call_in_worker(printer_for_sheet, lambda printer: _ask_print(panel, str(printer)), "Looking up the printer.")


def confirm_save(panel: CalibrationPanel) -> None:
    panel.call_in_worker(_save_body, lambda body: _ask_save(panel, str(body)), "Scoring the session scans.")


def confirm_new_session(panel: CalibrationPanel) -> None:
    body = "Moves the current session scans to data/calibration/archive. The saved profile is not changed."
    panel.app.push_screen(
        ConfirmScreen("Start a new session?", body, "Archive scans"),
        lambda ok: _then(panel, ok, new_session, "Archiving the session."),
    )


def _ask_print(panel: CalibrationPanel, printer: str) -> None:
    panel.app.push_screen(
        ConfirmScreen("Print the calibration sheet?", _PRINT_BODY.format(printer=printer), "Send one job"),
        lambda ok: _then(panel, ok, lambda: print_once(printer), "Sending one job. Waiting for the printer."),
    )


def _ask_save(panel: CalibrationPanel, body: str) -> None:
    panel.app.push_screen(
        ConfirmScreen("Save the density profile?", body, "Save profile"),
        lambda ok: _then(panel, ok, save_profile, "Saving the profile."),
    )


def _save_body() -> str:
    views = coverage(session_records()).views
    warning = "" if views >= _NEEDED else _INCOMPLETE.format(views=views, needed=_NEEDED)
    return save_preview() + warning


def _then(panel: CalibrationPanel, confirmed: bool | None, action: Callable[[], str], pending: str) -> None:
    if confirmed:
        panel.run_action(action, pending)
    else:
        panel.run_action(lambda: "Cancelled. Nothing was changed.", "Cancelled.")
