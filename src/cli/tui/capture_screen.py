import threading
from pathlib import Path

from textual import work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widget import Widget
from textual.widgets import Button, Checkbox, Input, Label, Select, Static

from common.config_store import list_profiles
from common.cups_client import list_printers
from common.device_config import get_scanner_settings


class CaptureScreen(Widget):

    def __init__(self) -> None:
        super().__init__()
        self._prompt_event = threading.Event()
        self._input_path: Path | None = None

    def compose(self) -> ComposeResult:
        prof_opts = [(n, n) for n, _ in list_profiles()]
        pr_opts = [(p.name, p.name) for p in list_printers()]
        scanner = get_scanner_settings()
        with VerticalScroll(classes="form-container"):
            yield Static("Guided Print + Scan Capture", classes="screen-title")
            with Vertical(classes="section"):
                yield Static("Source", classes="section-title")
                yield Checkbox("Generate random test data", id="chk-generate")
                yield Label("Input File", id="lbl-input")
                with Horizontal(classes="picker-row", id="row-input"):
                    yield Static("[dim]No file selected[/dim]", id="input-file-label")
                    yield Button("Browse...", id="input-file-browse")
                yield Label("Pages of test data", id="lbl-pages")
                yield Input(value="1", id="input-pages")
            with Vertical(classes="section"):
                yield Static("Hardware", classes="section-title")
                with Horizontal(classes="form-row"):
                    with Vertical(classes="form-col"):
                        yield Label("Profile")
                        yield Select(prof_opts, prompt="Select profile", id="profile-select")
                    with Vertical(classes="form-col"):
                        yield Label("Printer")
                        yield Select(pr_opts, prompt="Select printer", id="printer-select")
                with Horizontal(classes="form-row"):
                    with Vertical(classes="form-col"):
                        yield Label("Scanner Device")
                        yield Input(value=str(scanner.get("device", "")), id="scanner-input")
                    with Vertical(classes="form-col"):
                        yield Label("Scans per Page")
                        yield Input(value="3", id="scans-input")
            with Vertical(classes="section"):
                yield Static("Security", classes="section-title")
                yield Label("Password (optional)")
                yield Input(placeholder="encryption password", password=True, id="password-input")
            with Horizontal(classes="button-bar"):
                yield Button("Start Capture", variant="primary", id="btn-start", disabled=True)
                yield Button("Continue Scan", variant="warning", id="btn-continue", disabled=True)
            yield Static("", id="status")

    def on_mount(self) -> None:
        self._set_generate_mode(False)

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        if event.checkbox.id == "chk-generate":
            self._set_generate_mode(event.value)
            self._check_ready()

    def _set_generate_mode(self, gen: bool) -> None:
        self.query_one("#lbl-input", Label).display = not gen
        self.query_one("#row-input", Horizontal).display = not gen
        self.query_one("#lbl-pages", Label).display = gen
        self.query_one("#input-pages", Input).display = gen

    def on_input_changed(self, event: Input.Changed) -> None:
        self._check_ready()

    def on_select_changed(self, event: Select.Changed) -> None:
        self._check_ready()

    def _check_ready(self) -> None:
        has_profile = self.query_one("#profile-select", Select).value != Select.BLANK
        has_printer = self.query_one("#printer-select", Select).value != Select.BLANK
        if self.query_one("#chk-generate", Checkbox).value:
            ready = has_profile and has_printer
        else:
            ready = has_profile and has_printer and self._input_path is not None and self._input_path.is_file()
        self.query_one("#btn-start", Button).disabled = not ready

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-start":
            self.query_one("#btn-start", Button).disabled = True
            self._run_capture()
        elif event.button.id == "btn-continue":
            self.query_one("#btn-continue", Button).disabled = True
            self._prompt_event.set()
        elif event.button.id == "input-file-browse":
            from cli.tui.file_picker import FilePickerScreen
            self.app.push_screen(FilePickerScreen(mode="file"), callback=self._on_file_picked)

    def _on_file_picked(self, result: Path | None) -> None:
        if result is None:
            return
        self._input_path = result
        self.query_one("#input-file-label", Static).update(str(result))
        self._check_ready()

    def _blocking_prompt(self, msg: str) -> bool:
        self._prompt_event.clear()
        self.app.call_from_thread(self._show_prompt, msg)
        self._prompt_event.wait()
        return True

    def _show_prompt(self, msg: str) -> None:
        self.query_one("#status", Static).update(f"[bold yellow]{msg}[/bold yellow]")
        self.query_one("#btn-continue", Button).disabled = False

    @work(thread=True)
    def _run_capture(self) -> None:
        try:
            from cli.tui.capture_worker import run_full_capture
            on_s = lambda m: self.app.call_from_thread(self._update_status, m)
            msg = run_full_capture(
                profile=str(self.query_one("#profile-select", Select).value),
                printer=str(self.query_one("#printer-select", Select).value),
                scanner_device=self.query_one("#scanner-input", Input).value,
                scanner_settings=get_scanner_settings(),
                scans_per_page=int(self.query_one("#scans-input", Input).value or "3"),
                passphrase=self.query_one("#password-input", Input).value or None,
                generate=self.query_one("#chk-generate", Checkbox).value,
                input_path=self._input_path,
                generate_pages=int(self.query_one("#input-pages", Input).value or "1"),
                on_status=on_s, on_prompt=self._blocking_prompt,
            )
        except Exception as e:
            msg = f"[bold red]Error: {e}[/bold red]"
        self.app.call_from_thread(self._finish, msg)

    def _update_status(self, msg: str) -> None:
        self.query_one("#status", Static).update(msg)

    def _finish(self, msg: str) -> None:
        self._update_status(msg)
        self.query_one("#btn-start", Button).disabled = False
        self.query_one("#btn-continue", Button).disabled = True
