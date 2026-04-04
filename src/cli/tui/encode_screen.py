from pathlib import Path

from textual import work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widget import Widget
from textual.widgets import Button, Input, Label, ProgressBar, Select, Static

from common.config import PaperClipConfig
from common.config_store import list_profiles, load_profile
from common.page_layout import data_capacity_bytes
from common.paper_sizes import DEFAULT_PAPER_SIZE, config_with_page_dimensions, paper_size_options
from serialization.encode.pipeline import encode


class EncodeScreen(Widget):

    def __init__(self) -> None:
        super().__init__()
        self._config: PaperClipConfig | None = None
        self._profile_name: str = "custom"
        self._paper_size: str = DEFAULT_PAPER_SIZE
        self._input_path: Path | None = None
        self._passphrase: str | None = None

    def compose(self) -> ComposeResult:
        profiles = list_profiles()
        options = [(name, name) for name, _ in profiles]
        with VerticalScroll(classes="form-container"):
            yield Static("Encode File to Paper", classes="screen-title")
            with Vertical(classes="section"):
                yield Static("Profile & Paper", classes="section-title")
                with Horizontal(classes="form-row"):
                    with Vertical(classes="form-col"):
                        yield Label("Profile")
                        yield Select(options, prompt="Select profile", id="config-select")
                    with Vertical(classes="form-col"):
                        yield Label("Paper Size")
                        yield Select(paper_size_options(), value=DEFAULT_PAPER_SIZE, id="paper-select")
                yield Static("", id="config-details", classes="details-panel")
            with Vertical(classes="section"):
                yield Static("Input", classes="section-title")
                yield Label("File")
                with Horizontal(classes="picker-row"):
                    yield Static("[dim]No file selected[/dim]", id="input-file-label")
                    yield Button("Browse...", id="input-file-browse")
                yield Label("Password (leave empty for no encryption)")
                yield Input(placeholder="optional encryption password", password=True, id="password-input")
            yield Static("", id="encoding-plan", classes="details-panel")
            with Horizontal(classes="button-bar"):
                yield Button("Encode", variant="primary", id="btn-encode", disabled=True)
            yield ProgressBar(id="progress")
            yield Static("", id="status")

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.value == Select.BLANK:
            return
        if event.select.id == "config-select":
            try:
                self._config = load_profile(str(event.value))
                self._profile_name = str(event.value)
                self._apply_paper_size()
            except Exception as e:
                self._config = None
                self._update_plan()
                self.query_one("#config-details", Static).update(f"[red]Error: {e}[/red]")
        elif event.select.id == "paper-select":
            self._paper_size = str(event.value)
            self._apply_paper_size()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "password-input":
            self._passphrase = event.value or None
        self._update_plan()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-encode":
            self.query_one("#btn-encode", Button).disabled = True
            self._run_encode()
        elif event.button.id == "input-file-browse":
            from cli.tui.file_picker import FilePickerScreen
            self.app.push_screen(FilePickerScreen(mode="file"), callback=self._on_file_picked)

    def _on_file_picked(self, result: Path | None) -> None:
        if result is None:
            return
        self._input_path = result
        self.query_one("#input-file-label", Static).update(str(result))
        self._update_plan()

    def _apply_paper_size(self) -> None:
        if not self._config:
            return
        from cli.tui.encode_helpers import format_config_details
        try:
            self._config = config_with_page_dimensions(self._config, self._paper_size)
        except ValueError:
            pass
        self.query_one("#config-details", Static).update(format_config_details(self._config))
        self._update_plan()

    def _update_plan(self) -> None:
        plan = self.query_one("#encoding-plan", Static)
        btn = self.query_one("#btn-encode", Button)
        if not self._config or not self._input_path:
            plan.update("[dim]Select a profile and input file to see encoding plan[/dim]")
            btn.disabled = True
            return
        from cli.tui.encode_helpers import format_encoding_plan
        plan.update(format_encoding_plan(self._config, self._input_path))
        btn.disabled = False

    @work(thread=True)
    def _run_encode(self) -> None:
        try:
            from common.config import FLAG_ENCRYPTED, ALGO_FIELDS
            from common.data_store import create_job, digital_dir
            config, input_path, passphrase = self._config, self._input_path, self._passphrase
            flags = FLAG_ENCRYPTED if passphrase else 0
            file_size = input_path.stat().st_size
            total_pages = max(1, -(-file_size // data_capacity_bytes(config)))
            config_dict = {k: getattr(config, k) for k in ALGO_FIELDS}
            job_dir = create_job(input_path.name, self._profile_name, config_dict, total_pages)
            output_base = digital_dir(job_dir) / "page"

            def on_page(idx: int, total: int, path: Path | None) -> None:
                self.app.call_from_thread(self._set_progress, ((idx + 1) / total) * 100, f"Page {idx+1}/{total}")

            png_paths = encode(
                input_path, output_base, config,
                on_page_complete=on_page, flags=flags, passphrase=passphrase,
            )
            listing = "\n".join(str(p) for p in png_paths)
            msg = f"[bold green]Complete - {len(png_paths)} page(s):\n{listing}\nJob: {job_dir}[/bold green]"
        except Exception as e:
            msg = f"[bold red]Error: {e}[/bold red]"
        self.app.call_from_thread(self._set_progress, 100, msg, True)

    def _set_progress(self, pct: float, msg: str, done: bool = False) -> None:
        self.query_one("#progress", ProgressBar).update(total=100, progress=100 if done else pct)
        self.query_one("#status", Static).update(msg)
        if done:
            self.query_one("#btn-encode", Button).disabled = False
