from __future__ import annotations

from pathlib import Path

from textual import work
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Button, Static

from cli.tui.nav_messages import OpenPanel
from cli.tui.option_picker_screen import OptionPickerScreen
from cli.tui.scan_jobs import ScanJobContext
from cli.tui.scan_screen_layout import compose_scan_screen, format_scanner_state
from cli.tui.scan_screen_workers import discover_into, scan_page_into, start_job_into
from cli.tui.scan_worker import label_for_device


def _pick_label(options: list[tuple[str, str]], value: str | None) -> str:
    if not options:
        return "[dim]No scanners found[/dim]"
    if not value:
        return "[dim]Select...[/dim]"
    return label_for_device(options, value)


class ScanScreen(Widget):

    def __init__(self) -> None:
        super().__init__()
        self._scanner_options: list[tuple[str, str]] = []
        self._scanner_device: str | None = None
        self._max_dpi: int | None = None
        self._job: ScanJobContext | None = None
        self._page_count: int = 0
        self._last_saved: str = ""
        self._finished_job_id: str | None = None

    def compose(self) -> ComposeResult:
        yield from compose_scan_screen()

    def on_mount(self) -> None:
        self._discover()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "btn-scan-refresh":
            self._discover()
        elif bid == "scan-scanner-pick" and self._scanner_options:
            self.app.push_screen(OptionPickerScreen("Scanner", self._scanner_options), self._on_scanner_picked)
        elif bid == "btn-scan-start" and self._scanner_device and self._job is None:
            self.set_status("[bold]Starting the scan job (resolving the maximum DPI)...[/bold]")
            self._start_job(self._scanner_device)
        elif bid == "btn-scan-next" and self._job is not None and self._scanner_device:
            self.query_one("#btn-scan-next", Button).disabled = True
            self._scan_next_page(self._job, self._scanner_device, self._max_dpi)
        elif bid == "btn-scan-finish":
            self._finish_job()
        elif bid == "btn-scan-decode" and self._finished_job_id:
            self.post_message(OpenPanel("nav-decode", self._finished_job_id))

    def _on_scanner_picked(self, result: object | None) -> None:
        if result is None:
            return
        self._scanner_device = str(result)
        self._max_dpi = None
        self._refresh()

    @work(thread=True)
    def _discover(self) -> None:
        discover_into(self)

    @work(thread=True)
    def _start_job(self, device: str) -> None:
        start_job_into(self, device)

    @work(thread=True)
    def _scan_next_page(self, job: ScanJobContext, device: str, max_dpi: int | None) -> None:
        scan_page_into(self, job, device, max_dpi)

    def apply_discovery(self, options: list[tuple[str, str]], initial: str | None) -> None:
        self._scanner_options, self._scanner_device = options, initial
        self._max_dpi, self._job, self._page_count, self._last_saved = None, None, 0, ""
        self._refresh()
        self.set_status("" if options else "[yellow]No scanners detected.[/yellow]")

    def apply_started(self, job: ScanJobContext, max_dpi: int) -> None:
        self._job, self._max_dpi, self._page_count, self._last_saved = job, max_dpi, 0, ""
        self._refresh()
        self.set_status(f"[green]Started scan job {job.job_id} at {max_dpi} DPI. Place page 1 and press Scan Next Page.[/green]")

    def apply_scanned(self, path: Path, dpi: int) -> None:
        self._page_count += 1
        self._last_saved = str(path)
        self._refresh()
        self.set_status(f"[green]Saved {path.name} at {dpi} DPI. Place the next page, or press Finish.[/green]")

    def apply_scan_failed(self, message: str) -> None:
        self._refresh()
        self.set_status(message)

    def _finish_job(self) -> None:
        if self._job is None:
            return
        finished, pages = self._job.job_id, self._page_count
        self._finished_job_id = finished if pages else self._finished_job_id
        self._job, self._page_count, self._last_saved = None, 0, ""
        self._refresh()
        hint = " Press Decode this job to read it back." if pages else ""
        self.set_status(f"[green]Finished scan job {finished} with {pages} page(s).{hint}[/green]")

    def _refresh(self) -> None:
        button = self.query_one("#scan-scanner-pick", Button)
        button.label = _pick_label(self._scanner_options, self._scanner_device)
        button.disabled = not self._scanner_options
        self.query_one("#scan-job-details", Static).update(format_scanner_state(
            scanner_label=label_for_device(self._scanner_options, self._scanner_device),
            max_dpi=self._max_dpi,
            job_id=self._job.job_id if self._job else None,
            page_count=self._page_count,
            last_path=self._last_saved,
        ))
        has_scanner, has_job = self._scanner_device is not None, self._job is not None
        self.query_one("#btn-scan-start", Button).disabled = (not has_scanner) or has_job
        self.query_one("#btn-scan-next", Button).disabled = not (has_scanner and has_job)
        self.query_one("#btn-scan-finish", Button).disabled = not has_job
        self.query_one("#btn-scan-decode", Button).disabled = self._finished_job_id is None

    def set_status(self, text: str) -> None:
        self.query_one("#scan-status", Static).update(text)
