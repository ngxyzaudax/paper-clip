from __future__ import annotations

from functools import partial

from textual import work
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Button, Static

from cli.tui.confirm_screen import ConfirmScreen
from cli.tui.devices_worker import pick_button_label
from cli.tui.option_picker_screen import OptionPickerScreen
from cli.tui.print_form import PrintForm, load_print_form, submit_print_job
from cli.tui.print_jobs import PrintJob
from cli.tui.print_screen_layout import DUPLEX_OPTIONS, compose_print_screen, duplex_label, format_job_details
from cli.tui.print_screen_state import find_job, preferred_job, print_confirm_body
from common.types import PrinterInfo


class PrintScreen(Widget):

    def __init__(self, job_id: str | None = None) -> None:
        super().__init__()
        self._printers: list[PrinterInfo] = []
        self._jobs: list[PrintJob] = []
        self._printer_options: list[tuple[str, str]] = []
        self._job_options: list[tuple[str, str]] = []
        self._printer_name: str | None = None
        self._job_id: str | None = None
        self._wanted_job = job_id
        self._duplex: bool = False
        self._sending = False

    def compose(self) -> ComposeResult:
        yield from compose_print_screen()

    def on_mount(self) -> None:
        self._discover()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "btn-print-refresh":
            self._discover()
        elif bid == "print-printer-pick" and self._printer_options:
            self._pick("Printer", self._printer_options, "printer")
        elif bid == "print-job-pick" and self._job_options:
            self._pick("Job", self._job_options, "job")
        elif bid == "print-duplex-pick":
            self._pick("Duplex", DUPLEX_OPTIONS, "duplex")
        elif bid == "btn-print-submit":
            self._confirm_print()

    def _pick(self, title: str, options: list[tuple[str, str]], kind: str) -> None:
        self.app.push_screen(OptionPickerScreen(title, options), partial(self._on_option_picked, kind))

    def _on_option_picked(self, kind: str, result: object | None) -> None:
        if result is None:
            return
        if kind == "printer":
            self._printer_name = str(result)
        elif kind == "job":
            self._job_id = str(result)
        elif kind == "duplex":
            self._duplex = result == "on"
        self._refresh()

    @work(thread=True)
    def _discover(self) -> None:
        self._status_from_thread("[bold]Discovering printers and jobs...[/bold]")
        form = load_print_form()
        self.app.call_from_thread(self._apply_form, form)

    def _apply_form(self, form: PrintForm) -> None:
        self._printers = form.printers
        self._jobs = form.jobs
        self._printer_options = form.printer_options
        self._job_options = form.job_options
        self._printer_name = form.printer_name
        self._job_id = preferred_job(form.job_options, self._wanted_job, form.job_id)
        self._refresh()
        self._status("")

    def _selected_job(self) -> PrintJob | None:
        return find_job(self._jobs, self._job_id)

    def _refresh(self) -> None:
        self._refresh_labels()
        self.query_one("#print-job-details", Static).update(format_job_details(self._selected_job(), self._duplex))
        can_print = self._printer_name is not None and self._selected_job() is not None
        self.query_one("#btn-print-submit", Button).disabled = self._sending or not can_print

    def _refresh_labels(self) -> None:
        printer_btn = self.query_one("#print-printer-pick", Button)
        job_btn = self.query_one("#print-job-pick", Button)
        printer_btn.label = pick_button_label(
            self._printer_options, self._printer_name, absent_message="[dim]No printers found[/dim]",
        )
        job_btn.label = pick_button_label(self._job_options, self._job_id, absent_message="[dim]No jobs found[/dim]")
        self.query_one("#print-duplex-pick", Button).label = duplex_label(self._duplex)
        printer_btn.disabled = not self._printer_options
        job_btn.disabled = not self._job_options

    def _confirm_print(self) -> None:
        job, printer = self._selected_job(), self._printer_name
        if job is None or not printer or self._sending:
            return
        self.app.push_screen(
            ConfirmScreen("Print this job?", print_confirm_body(job, printer, self._duplex), "Print"),
            lambda ok: self._start_print(job, printer) if ok else None,
        )

    def _start_print(self, job: PrintJob, printer: str) -> None:
        self._sending = True
        self._refresh()
        self._status("[bold]Submitting print job...[/bold]")
        self._print_job(job, printer, self._duplex)

    @work(thread=True)
    def _print_job(self, job: PrintJob, printer: str, duplex: bool) -> None:
        try:
            message = submit_print_job(printer, job, duplex)
        except Exception as exc:
            message = f"[red]Print error: {exc}[/red]"
        self.app.call_from_thread(self._print_done, message)

    def _print_done(self, message: str) -> None:
        self._sending = False
        self._refresh()
        self._status(message)

    def _status(self, message: str) -> None:
        self.query_one("#print-status", Static).update(message)

    def _status_from_thread(self, message: str) -> None:
        self.app.call_from_thread(self._status, message)
