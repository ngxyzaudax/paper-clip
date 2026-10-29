from __future__ import annotations

from functools import partial
from pathlib import Path

from textual import work
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Button, Static

from cli.tui.option_picker_screen import OptionPickerScreen
from cli.tui.scan_jobs import (
    ScanJobContext,
    next_scan_path,
    start_scan_job,
    update_scan_job_metadata,
)
from cli.tui.scan_screen_layout import compose_scan_screen, format_scanner_state
from cli.tui.scan_worker import (
    discover_scanners_for_scan,
    label_for_device,
    resolve_max_dpi,
)
from common.device_config import get_scanner_settings
from common.scan_capture import capture_page


def _pick_label(
    options: list[tuple[str, str]],
    value: str | None,
) -> str:
    if not options:
        return "[dim]No scanners found[/dim]"
    if not value:
        return "[dim]Select…[/dim]"
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

    def compose(self) -> ComposeResult:
        yield from compose_scan_screen()

    def on_mount(self) -> None:
        self._discover()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "btn-scan-refresh":
            self._discover()
        elif bid == "scan-scanner-pick" and self._scanner_options:
            self.app.push_screen(
                OptionPickerScreen("Scanner", self._scanner_options),
                partial(self._on_scanner_picked),
            )
        elif bid == "btn-scan-start":
            self._start_job()
        elif bid == "btn-scan-next":
            self._scan_next_page()
        elif bid == "btn-scan-finish":
            self._finish_job()

    def _on_scanner_picked(self, result: object | None) -> None:
        if result is None:
            return
        self._scanner_device = str(result)
        self._max_dpi = None
        self._refresh_labels()
        self._refresh_actions()
        self._refresh_details()

    @work(thread=True)
    def _discover(self) -> None:
        self._set_status_threadsafe("[bold]Discovering scanners…[/bold]")
        options, initial = discover_scanners_for_scan()

        def _update() -> None:
            self._scanner_options = options
            self._scanner_device = initial
            self._max_dpi = None
            self._job = None
            self._page_count = 0
            self._last_saved = ""
            self._refresh_labels()
            self._refresh_details()
            self._refresh_actions()
            empty = "[yellow]No scanners detected.[/yellow]" if not options else ""
            self._set_status(empty)

        self.app.call_from_thread(_update)

    def _start_job(self) -> None:
        device = self._scanner_device
        if not device or self._job is not None:
            return
        self._set_status("[bold]Starting scan job (resolving max DPI)…[/bold]")
        self._start_job_worker(device)

    @work(thread=True)
    def _start_job_worker(self, device: str) -> None:
        max_dpi = resolve_max_dpi(device)
        if max_dpi is None:
            saved_dpi = int(get_scanner_settings().get("dpi", 0) or 0)
            max_dpi = saved_dpi if saved_dpi > 0 else 0
        if max_dpi <= 0:
            self._set_status_threadsafe(
                "[red]Could not resolve scanner DPI. Verify scanner is online.[/red]",
            )
            return
        try:
            ctx = start_scan_job(device, max_dpi)
        except Exception as exc:
            self._set_status_threadsafe(f"[red]Could not start job: {exc}[/red]")
            return

        def _update() -> None:
            self._job = ctx
            self._max_dpi = max_dpi
            self._page_count = 0
            self._last_saved = ""
            self._refresh_details()
            self._refresh_actions()
            self._set_status(
                f"[green]Started scan job {ctx.job_id} at {max_dpi} DPI[/green]",
            )

        self.app.call_from_thread(_update)

    @work(thread=True)
    def _scan_next_page(self) -> None:
        job = self._job
        device = self._scanner_device
        if job is None or not device:
            return
        target = next_scan_path(job.job_dir)
        self._set_status_threadsafe(
            f"[bold]Scanning page {target.stem}… (max DPI={self._max_dpi})[/bold]",
        )
        try:
            result = capture_page(device, target, self._max_dpi)
        except Exception as exc:
            self._set_status_threadsafe(f"[red]Scan failed: {exc}[/red]")
            return
        try:
            update_scan_job_metadata(job.job_dir, result.dpi, result.mode)
        except Exception:
            pass

        def _update() -> None:
            self._page_count += 1
            self._last_saved = str(result.target_path)
            self._refresh_details()
            self._refresh_actions()
            self._set_status(
                f"[green]Saved {Path(result.target_path).name} at {result.dpi} DPI[/green]",
            )

        self.app.call_from_thread(_update)

    def _finish_job(self) -> None:
        if self._job is None:
            return
        finished_id = self._job.job_id
        self._job = None
        self._page_count = 0
        self._last_saved = ""
        self._refresh_details()
        self._refresh_actions()
        self._set_status(f"[green]Finished scan job {finished_id}[/green]")

    def _refresh_labels(self) -> None:
        btn = self.query_one("#scan-scanner-pick", Button)
        btn.label = _pick_label(self._scanner_options, self._scanner_device)
        btn.disabled = not self._scanner_options

    def _refresh_details(self) -> None:
        text = format_scanner_state(
            scanner_label=label_for_device(self._scanner_options, self._scanner_device),
            max_dpi=self._max_dpi,
            job_id=self._job.job_id if self._job else None,
            page_count=self._page_count,
            last_path=self._last_saved,
        )
        self.query_one("#scan-job-details", Static).update(text)

    def _refresh_actions(self) -> None:
        has_scanner = self._scanner_device is not None
        has_job = self._job is not None
        self.query_one("#btn-scan-start", Button).disabled = (not has_scanner) or has_job
        self.query_one("#btn-scan-next", Button).disabled = not (has_scanner and has_job)
        self.query_one("#btn-scan-finish", Button).disabled = not has_job

    def _set_status(self, text: str) -> None:
        self.query_one("#scan-status", Static).update(text)

    def _set_status_threadsafe(self, text: str) -> None:
        self.app.call_from_thread(self.query_one("#scan-status", Static).update, text)
