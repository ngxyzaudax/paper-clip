from __future__ import annotations

from functools import partial

from textual import work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widget import Widget
from textual.widgets import Button, Label, Static

from cli.tui.option_picker_screen import OptionPickerScreen
from cli.tui.print_jobs import PrintJob, discover_print_jobs, job_option_label
from common.cups_client import list_printers, print_files
from common.device_config import get_printer_settings
from common.types import PrinterInfo


def _pick_label(
    options: list[tuple[str, str]],
    value: str | None,
    empty_label: str,
) -> str:
    if not options:
        return empty_label
    if not value:
        return "[dim]Select…[/dim]"
    for label, key in options:
        if key == value:
            return label
    return value


def _format_job_details(job: PrintJob | None) -> str:
    if job is None:
        return "[dim]Select a job to preview pages[/dim]"
    page_lines = "\n".join(f"  - {p.name}" for p in job.page_paths[:20])
    if len(job.page_paths) > 20:
        page_lines += f"\n  ... ({len(job.page_paths) - 20} more)"
    source = job.source_file if job.source_file else "(unknown source)"
    created = job.created if job.created else "(unknown)"
    paper = job.paper_size if job.paper_size else "(unknown)"
    return (
        f"[bold]Job[/bold]: {job.job_id}\n"
        f"[bold]Source[/bold]: {source}\n"
        f"[bold]Created[/bold]: {created}\n"
        f"[bold]Paper[/bold]: {paper}\n"
        f"[bold]Pages[/bold]: {len(job.page_paths)}\n\n"
        f"[bold]Files[/bold]\n{page_lines}"
    )


class PrintScreen(Widget):

    def __init__(self) -> None:
        super().__init__()
        self._printers: list[PrinterInfo] = []
        self._jobs: list[PrintJob] = []
        self._printer_options: list[tuple[str, str]] = []
        self._job_options: list[tuple[str, str]] = []
        self._printer_name: str | None = None
        self._job_id: str | None = None

    def compose(self) -> ComposeResult:
        with Vertical(classes="encode-screen-layout form-container"):
            with Horizontal(classes="encode-split"):
                with Vertical(classes="encode-form-col"):
                    yield Static("Print jobs", classes="encode-panel-title")
                    with Vertical(classes="section"):
                        with VerticalScroll(classes="encode-form-scroll"):
                            with Horizontal(classes="form-row"):
                                with Vertical(classes="form-col"):
                                    yield Label("Printer")
                                    yield Button(
                                        "[dim]Discovering…[/dim]",
                                        id="print-printer-pick",
                                        compact=True,
                                        disabled=True,
                                    )
                            with Horizontal(classes="form-row"):
                                with Vertical(classes="form-col"):
                                    yield Label("Job")
                                    yield Button(
                                        "[dim]Discovering…[/dim]",
                                        id="print-job-pick",
                                        compact=True,
                                        disabled=True,
                                    )
                with Vertical(classes="encode-info-col"):
                    yield Static("Job details", classes="encode-panel-title")
                    with Vertical(classes="section"):
                        with VerticalScroll(classes="encode-info-scroll"):
                            yield Static(
                                "[dim]Loading jobs…[/dim]",
                                id="print-job-details",
                                classes="details-panel",
                            )
            with VerticalScroll(classes="encode-bottom-scroll"):
                with Horizontal(classes="button-bar"):
                    yield Button("Refresh", id="btn-print-refresh", compact=True)
                    yield Button(
                        "Print Job",
                        id="btn-print-submit",
                        variant="primary",
                        compact=True,
                        disabled=True,
                    )
                yield Static("", id="print-status")

    def on_mount(self) -> None:
        self._discover()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "btn-print-refresh":
            self._discover()
        elif bid == "print-printer-pick":
            if self._printer_options:
                self.app.push_screen(
                    OptionPickerScreen("Printer", self._printer_options),
                    partial(self._on_option_picked, "printer"),
                )
        elif bid == "print-job-pick":
            if self._job_options:
                self.app.push_screen(
                    OptionPickerScreen("Job", self._job_options),
                    partial(self._on_option_picked, "job"),
                )
        elif bid == "btn-print-submit":
            self._print_selected_job()

    def _on_option_picked(self, kind: str, result: object | None) -> None:
        if result is None:
            return
        if kind == "printer":
            self._printer_name = str(result)
        else:
            self._job_id = str(result)
        self._refresh_labels()
        self._refresh_details()
        self._refresh_actions()

    @work(thread=True)
    def _discover(self) -> None:
        self.app.call_from_thread(
            self.query_one("#print-status", Static).update,
            "[bold]Discovering printers and jobs...[/bold]",
        )
        printers = list_printers()
        jobs = discover_print_jobs()
        saved_printer = get_printer_settings().get("name", "")

        printer_options = [
            (f"{p.name} ({p.state})" + (" [default]" if p.is_default else ""), p.name)
            for p in printers
        ]
        printer_name = None
        if saved_printer and any(name == saved_printer for _, name in printer_options):
            printer_name = saved_printer
        elif printers:
            default = next((p.name for p in printers if p.is_default), None)
            printer_name = default or printers[0].name

        job_options = [(job_option_label(job), job.job_id) for job in jobs]
        job_id = job_options[0][1] if job_options else None

        def _update() -> None:
            self._printers = printers
            self._jobs = jobs
            self._printer_options = printer_options
            self._job_options = job_options
            self._printer_name = printer_name
            self._job_id = job_id
            self._refresh_labels()
            self._refresh_details()
            self._refresh_actions()
            self.query_one("#print-status", Static).update("")

        self.app.call_from_thread(_update)

    def _selected_job(self) -> PrintJob | None:
        if not self._job_id:
            return None
        for job in self._jobs:
            if job.job_id == self._job_id:
                return job
        return None

    def _refresh_labels(self) -> None:
        printer_btn = self.query_one("#print-printer-pick", Button)
        job_btn = self.query_one("#print-job-pick", Button)
        printer_btn.label = _pick_label(
            self._printer_options,
            self._printer_name,
            "[dim]No printers found[/dim]",
        )
        job_btn.label = _pick_label(
            self._job_options,
            self._job_id,
            "[dim]No jobs found[/dim]",
        )
        printer_btn.disabled = not self._printer_options
        job_btn.disabled = not self._job_options

    def _refresh_details(self) -> None:
        self.query_one("#print-job-details", Static).update(
            _format_job_details(self._selected_job()),
        )

    def _refresh_actions(self) -> None:
        can_print = self._printer_name is not None and self._selected_job() is not None
        self.query_one("#btn-print-submit", Button).disabled = not can_print

    @work(thread=True)
    def _print_selected_job(self) -> None:
        job = self._selected_job()
        printer = self._printer_name
        if job is None or not printer:
            return
        self.app.call_from_thread(
            self.query_one("#print-status", Static).update,
            "[bold]Submitting print job...[/bold]",
        )
        try:
            ids = print_files(printer, list(job.page_paths), f"paper-clip {job.job_id}")
            ids_text = ", ".join(str(i) for i in ids)
            self.app.call_from_thread(
                self.query_one("#print-status", Static).update,
                f"[bold green]Submitted {len(ids)} page(s) to {printer}. Job IDs: {ids_text}[/bold green]",
            )
        except Exception as exc:
            self.app.call_from_thread(
                self.query_one("#print-status", Static).update,
                f"[red]Print error: {exc}[/red]",
            )
