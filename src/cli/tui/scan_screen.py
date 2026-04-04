from pathlib import Path

from textual import work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widget import Widget
from textual.widgets import Button, Input, Label, ProgressBar, Select, Static


class ScanScreen(Widget):

    def __init__(self) -> None:
        super().__init__()
        self._output_dir: Path = Path("./scans")

    def compose(self) -> ComposeResult:
        with VerticalScroll(classes="form-container"):
            yield Static("Scan Pages", classes="screen-title")
            with Vertical(classes="section"):
                yield Static("Scanner", classes="section-title")
                with Horizontal(classes="form-row"):
                    with Vertical(classes="form-col"):
                        yield Label("Device")
                        yield Select([], prompt="Discovering scanners...", id="scanner-select")
                    with Vertical(classes="form-col"):
                        yield Label("DPI")
                        yield Select([], prompt="Select scanner first", id="dpi-select")
            with Vertical(classes="section"):
                yield Static("Output", classes="section-title")
                with Horizontal(classes="form-row"):
                    with Vertical(classes="form-col"):
                        yield Label("Number of Scans")
                        yield Input(value="3", id="count-input")
                    with Vertical(classes="form-col"):
                        yield Label("Output Directory")
                        with Horizontal(classes="picker-row"):
                            yield Static("./scans", id="output-dir-label")
                            yield Button("Browse...", id="output-dir-browse")
            with Horizontal(classes="button-bar"):
                yield Button("Scan", variant="primary", id="btn-scan", disabled=True)
            yield ProgressBar(id="progress")
            yield Static("", id="status")

    def on_mount(self) -> None:
        self._load_scanners()

    @work(thread=True)
    def _load_scanners(self) -> None:
        try:
            from cli.tui.scan_worker import discover_scanners
            options, initial, saved_dpi = discover_scanners()

            def _update() -> None:
                sel = self.query_one("#scanner-select", Select)
                sel.set_options(options)
                if initial != Select.BLANK:
                    sel.value = initial
                if not options:
                    self.query_one("#status", Static).update("[yellow]No scanners found[/yellow]")
                self._saved_dpi = saved_dpi
            self.app.call_from_thread(_update)
            if initial != Select.BLANK:
                self._load_dpi_options(str(initial))
        except Exception as e:
            self.app.call_from_thread(
                self.query_one("#status", Static).update,
                f"[red]Scanner discovery failed: {e}[/red]",
            )

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.value == Select.BLANK:
            return
        if event.select.id == "scanner-select":
            self._load_dpi_options(str(event.value))
        elif event.select.id == "dpi-select":
            self.query_one("#btn-scan", Button).disabled = False

    @work(thread=True)
    def _load_dpi_options(self, device_id: str) -> None:
        try:
            from cli.tui.scan_worker import load_dpi_options
            options, initial = load_dpi_options(device_id, getattr(self, "_saved_dpi", "1200"))

            def _update() -> None:
                sel = self.query_one("#dpi-select", Select)
                sel.set_options(options)
                if initial != Select.BLANK:
                    sel.value = initial
                self.query_one("#btn-scan", Button).disabled = False
            self.app.call_from_thread(_update)
        except Exception as e:
            self.app.call_from_thread(
                self.query_one("#status", Static).update,
                f"[red]Failed to load DPI options: {e}[/red]",
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-scan":
            self.query_one("#btn-scan", Button).disabled = True
            self.query_one("#status", Static).update("[bold]Scanning...[/bold]")
            self._run_scan()
        elif event.button.id == "output-dir-browse":
            from cli.tui.file_picker import FilePickerScreen
            self.app.push_screen(
                FilePickerScreen(mode="directory", title="Select output directory"),
                callback=self._on_dir_picked,
            )

    def _on_dir_picked(self, result: Path | None) -> None:
        if result is None:
            return
        self._output_dir = result
        self.query_one("#output-dir-label", Static).update(str(result))

    @work(thread=True)
    def _run_scan(self) -> None:
        try:
            from cli.tui.scan_worker import run_scan_session
            scanner_val = self.query_one("#scanner-select", Select).value
            dpi_val = self.query_one("#dpi-select", Select).value
            device = str(scanner_val) if scanner_val != Select.BLANK else ""
            dpi = int(dpi_val) if dpi_val != Select.BLANK else 1200
            count = int(self.query_one("#count-input", Input).value or "1")
            on_progress = lambda i, t: self.app.call_from_thread(self._update_progress, i, t)
            msg, _ = run_scan_session(device, dpi, count, self._output_dir.expanduser(), on_progress)
        except Exception as e:
            msg = f"[bold red]Scan error: {e}[/bold red]"
        self.app.call_from_thread(self._on_done, msg)

    def _update_progress(self, current: int, total: int) -> None:
        self.query_one("#progress", ProgressBar).update(total=total, progress=current)
        self.query_one("#status", Static).update(f"Scanning {current + 1}/{total}...")

    def _on_done(self, message: str) -> None:
        self.query_one("#progress", ProgressBar).update(total=100, progress=100)
        self.query_one("#status", Static).update(message)
        self.query_one("#btn-scan", Button).disabled = False
