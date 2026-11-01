from collections.abc import Callable

from textual import work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widget import Widget
from textual.widgets import Button, DataTable, LoadingIndicator, Static

from calibration.session_view import SessionView, session_view
from cli.tui.calibrate_confirm import confirm_new_session, confirm_print, confirm_save
from cli.tui.calibrate_flow import render_sheet, run_simulation, scan_view
from cli.tui.calibrate_style import CALIBRATE_CSS
from cli.tui.calibrate_view import apply_session_view
from common.device_error import DeviceError

ACTION_BUTTONS = (
    ("cal-render", "Render sheet", "primary"),
    ("cal-simulate", "Simulate", "default"),
    ("cal-print", "Print...", "warning"),
    ("cal-scan", "Scan view", "primary"),
    ("cal-save", "Save profile...", "success"),
    ("cal-new", "New session...", "default"),
)

_DIRECT = {
    "cal-render": (render_sheet, "Rendering both sides at 720 dpi."),
    "cal-simulate": (run_simulation, "Running the ink model on the sheet. Nothing is printed or saved."),
    "cal-scan": (scan_view, "Scanning at the scanner's resolution. Keep the lid closed."),
}

_RECOVERABLE = (DeviceError, OSError, ValueError, RuntimeError)


class CalibrateScreen(Widget):
    """Guided calibration: render, print once, scan both sides, review the limits, save."""

    DEFAULT_CSS = CALIBRATE_CSS

    def __init__(self) -> None:
        super().__init__()
        self.busy = False

    def compose(self) -> ComposeResult:
        yield Static("Density calibration", classes="encode-panel-title")
        with Horizontal(id="cal-body"):
            with VerticalScroll(id="cal-left"):
                yield Static("Steps", classes="cal-heading")
                yield Static("", id="cal-steps", markup=False)
                yield Static("Next", classes="cal-heading")
                yield Static("Reading the session...", id="cal-next", markup=False)
                yield Static("Scans", classes="cal-heading")
                yield Static("", id="cal-scans", markup=False)
            with Vertical(id="cal-right"):
                yield Static("Measured limits", classes="cal-heading")
                yield DataTable(id="cal-table", cursor_type="row", zebra_stripes=True)
                yield Static("", id="cal-summary", markup=False)
        with Horizontal(id="cal-status-row"):
            yield LoadingIndicator(id="cal-busy")
            yield Static("", id="cal-status", markup=False)
        with Horizontal(id="cal-actions"):
            for button_id, label, variant in ACTION_BUTTONS:
                yield Button(label, id=button_id, variant=variant, compact=True)

    def on_mount(self) -> None:
        self.run_action(lambda: "Ready.", "Reading the session.")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id or ""
        if self.busy:
            return
        if button_id in _DIRECT:
            action, pending = _DIRECT[button_id]
            self.run_action(action, pending)
        elif button_id == "cal-print":
            confirm_print(self)
        elif button_id == "cal-save":
            confirm_save(self)
        elif button_id == "cal-new":
            confirm_new_session(self)

    def run_action(self, action: Callable[[], str], pending: str) -> None:
        self.set_busy(True, pending)
        self._worker(action)

    @work(thread=True, exclusive=True, group="calibrate")
    def _worker(self, action: Callable[[], str]) -> None:
        try:
            message = action()
        except _RECOVERABLE as exc:
            message = f"Failed: {exc}"
        view = session_view()
        self.app.call_from_thread(self._finish, message, view)

    def _finish(self, message: str, view: SessionView) -> None:
        apply_session_view(self, view)
        self.set_busy(False, message)

    def set_busy(self, busy: bool, message: str) -> None:
        self.busy = busy
        self.query_one("#cal-busy", LoadingIndicator).set_class(busy, "busy")
        self.query_one("#cal-status", Static).update(message)
        for button in self.query("#cal-actions Button").results(Button):
            button.disabled = busy

    def call_in_worker(self, action: Callable[[], object], then: Callable[[object], None], pending: str) -> None:
        """Run a slow lookup off the UI thread, then continue on the UI thread with its result."""
        self.set_busy(True, pending)
        self._lookup(action, then)

    @work(thread=True, exclusive=True, group="calibrate")
    def _lookup(self, action: Callable[[], object], then: Callable[[object], None]) -> None:
        try:
            result = action()
        except _RECOVERABLE as exc:
            self.app.call_from_thread(self.set_busy, False, f"Failed: {exc}")
            return
        self.app.call_from_thread(self._continue, then, result)

    def _continue(self, then: Callable[[object], None], result: object) -> None:
        self.set_busy(False, "Waiting for confirmation.")
        then(result)
