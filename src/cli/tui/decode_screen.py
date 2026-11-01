from __future__ import annotations

from pathlib import Path

from textual import work
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Button, Input, LoadingIndicator, Static

from cli.tui.decode_flow import decode_error_text, decode_result_text, decode_source
from cli.tui.decode_screen_layout import DECODE_CSS, compose_decode_screen
from cli.tui.file_picker import FilePickerScreen
from cli.tui.option_picker_screen import OptionPickerScreen
from cli.tui.print_screen_state import preferred_job
from cli.tui.scan_job_list import ScanJob, discover_scan_jobs, scan_job_details, scan_job_option


class DecodeScreen(Widget):
    """Pick a scan job or folder, decode it in the background, and save the file under data/decoded."""

    DEFAULT_CSS = DECODE_CSS

    def __init__(self, job_id: str | None = None) -> None:
        super().__init__()
        self._wanted_job = job_id
        self._jobs: list[ScanJob] = []
        self._job_id: str | None = None
        self._folder: Path | None = None
        self.busy = False

    def compose(self) -> ComposeResult:
        yield from compose_decode_screen()

    def on_mount(self) -> None:
        self._load_jobs()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if self.busy:
            return
        if bid == "dec-refresh":
            self._load_jobs()
        elif bid == "dec-job-pick" and self._jobs:
            options = [scan_job_option(job) for job in self._jobs]
            self.app.push_screen(OptionPickerScreen("Scan job", options), self._on_job_picked)
        elif bid == "dec-browse":
            self.app.push_screen(FilePickerScreen(mode="directory"), self._on_folder_picked)
        elif bid == "dec-run" and (source := self._source()) is not None:
            self._set_busy(True, f"Decoding {source[1]}. Large jobs take a while.")
            self._decode(source[0], source[1], self.query_one("#dec-password", Input).value or None)

    def _load_jobs(self) -> None:
        self._jobs = discover_scan_jobs()
        options = [scan_job_option(job) for job in self._jobs]
        newest = options[0][1] if options else None
        self._job_id = preferred_job(options, self._wanted_job, newest) if self._folder is None else None
        self._refresh()

    def _on_job_picked(self, result: object | None) -> None:
        if result is not None:
            self._job_id, self._folder = str(result), None
            self._refresh()

    def _on_folder_picked(self, result: Path | None) -> None:
        if result is not None:
            self._folder, self._job_id = result, None
            self._refresh()

    def _selected(self) -> ScanJob | None:
        return next((job for job in self._jobs if job.job_id == self._job_id), None)

    def _source(self) -> tuple[Path, str] | None:
        if self._folder is not None:
            return self._folder, self._folder.name
        job = self._selected()
        return (job.folder, job.job_id) if job else None

    def _refresh(self) -> None:
        pick = self.query_one("#dec-job-pick", Button)
        pick.disabled = not self._jobs
        job = self._selected()
        pick.label = scan_job_option(job)[0] if job else ("Select..." if self._jobs else "[dim]No scan jobs yet[/dim]")
        self.query_one("#dec-run", Button).disabled = self.busy or self._source() is None
        self.query_one("#dec-details", Static).update(self._details(job))

    def _details(self, job: ScanJob | None) -> str:
        if self._folder is not None:
            return f"[bold]Folder[/bold]: {self._folder}"
        if job is not None:
            return scan_job_details(job)
        return "[dim]Scan pages on the Scan panel, or browse to a folder of scans.[/dim]"

    @work(thread=True, exclusive=True, group="decode")
    def _decode(self, source: Path, label: str, passphrase: str | None) -> None:
        try:
            message = decode_result_text(decode_source(source, label, passphrase))
        except Exception as exc:
            message = decode_error_text(exc)
        self.app.call_from_thread(self._set_busy, False, message)

    def _set_busy(self, busy: bool, message: str) -> None:
        self.busy = busy
        self.query_one("#dec-busy", LoadingIndicator).set_class(busy, "busy")
        self.query_one("#dec-status", Static).update(message)
        for button in self.query("Button").results(Button):
            button.disabled = busy
        if not busy:
            self._refresh()
