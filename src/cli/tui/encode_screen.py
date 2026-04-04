from __future__ import annotations

from pathlib import Path

from textual import work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.timer import Timer
from textual.widget import Widget
from textual.widgets import Button, Input, Label, ProgressBar, Select, Static

from cli.tui.tui_encoding import tui_encoding_config
from cli.tui.encode_helpers import format_encoding_info_panel, format_encoding_plan
from common.config import ALGO_FIELDS, PaperClipConfig, default_config
from common.data_store import create_job, digital_dir
from common.page_layout import data_capacity_bytes
from common.paper_sizes import DEFAULT_PAPER_SIZE, config_with_page_dimensions, paper_size_options
from serialization.encode.pipeline import encode


class EncodeScreen(Widget):

    def __init__(self) -> None:
        super().__init__()
        self._config: PaperClipConfig | None = None
        self._paper_size: str = DEFAULT_PAPER_SIZE
        self._input_path: Path | None = None
        self._passphrase: str | None = None
        self._rebuild_timer: Timer | None = None

    def compose(self) -> ComposeResult:
        dc = default_config()
        with Vertical(classes="encode-screen-layout form-container"):
            with Horizontal(classes="encode-split"):
                with Vertical(classes="encode-form-col"):
                    yield Static("Encoding settings", classes="encode-panel-title")
                    with Vertical(classes="section"):
                        with VerticalScroll(classes="encode-form-scroll"):
                            yield Label("Config TOML (optional)")
                            with Horizontal(classes="picker-row"):
                                yield Input(placeholder="path to paper_clip.toml", id="enc-config-path", compact=True)
                                yield Button("Browse...", id="enc-config-browse", compact=True)
                            with Horizontal(classes="form-row"):
                                with Vertical(classes="form-col"):
                                    yield Label("Colors")
                                    yield Input(value=str(dc.num_colors), id="enc-num-colors", compact=True)
                                with Vertical(classes="form-col"):
                                    yield Label("Cell px")
                                    yield Input(value=str(dc.cell_size_px), id="enc-cell-size", compact=True)
                            with Horizontal(classes="form-row"):
                                with Vertical(classes="form-col"):
                                    yield Label("Print DPI")
                                    yield Input(value=str(dc.print_dpi), id="enc-print-dpi", compact=True)
                                with Vertical(classes="form-col"):
                                    yield Label("RS redundancy")
                                    yield Input(value=str(dc.rs_redundancy), id="enc-rs", compact=True)
                            with Horizontal(classes="form-row"):
                                with Vertical(classes="form-col"):
                                    yield Label("Parity pages")
                                    yield Input(value=str(dc.redundancy_pages), id="enc-red-pages", compact=True)
                            with Horizontal(classes="form-row"):
                                yield Label("Margins mm")
                            with Horizontal(classes="form-row"):
                                with Vertical(classes="form-col"):
                                    yield Label("Top")
                                    yield Input(value=str(dc.margin_top_mm), id="enc-margin-t", compact=True)
                                with Vertical(classes="form-col"):
                                    yield Label("Right")
                                    yield Input(value=str(dc.margin_right_mm), id="enc-margin-r", compact=True)
                                with Vertical(classes="form-col"):
                                    yield Label("Bottom")
                                    yield Input(value=str(dc.margin_bottom_mm), id="enc-margin-b", compact=True)
                                with Vertical(classes="form-col"):
                                    yield Label("Left")
                                    yield Input(value=str(dc.margin_left_mm), id="enc-margin-l", compact=True)
                            with Horizontal(classes="form-row"):
                                with Vertical(classes="form-col"):
                                    yield Label("Paper size")
                                    yield Select(
                                        paper_size_options(),
                                        value=DEFAULT_PAPER_SIZE,
                                        id="paper-select",
                                        compact=True,
                                    )
                with Vertical(classes="encode-info-col"):
                    yield Static("Encoding info", classes="encode-panel-title")
                    with Vertical(classes="section"):
                        with VerticalScroll(classes="encode-info-scroll"):
                            yield Static("", id="encode-info-display", classes="details-panel")
            with VerticalScroll(classes="encode-bottom-scroll"):
                with Vertical(classes="section encode-input-section"):
                    yield Static("Input", classes="section-title")
                    with Horizontal(classes="picker-row"):
                        yield Static("[dim]No file selected[/dim]", id="input-file-label")
                        yield Button("Browse...", id="input-file-browse", compact=True)
                    with Vertical(classes="encode-password-block"):
                        yield Label("Password")
                        yield Input(
                            placeholder="optional; encrypts payload",
                            password=True,
                            id="password-input",
                            compact=True,
                        )
                yield Static("", id="encoding-plan", classes="details-panel")
                with Horizontal(classes="button-bar"):
                    yield Button(
                        "Encode",
                        variant="primary",
                        id="btn-encode",
                        disabled=True,
                        classes="encode-action-btn",
                        compact=True,
                    )
                yield ProgressBar(id="progress", total=100, show_eta=False)
                yield Static("", id="status")

    def on_mount(self) -> None:
        self._rebuild_config()

    def on_unmount(self) -> None:
        if self._rebuild_timer is not None:
            self._rebuild_timer.stop()
            self._rebuild_timer = None

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "password-input":
            self._passphrase = event.value or None
            return
        self._schedule_rebuild()

    def _schedule_rebuild(self) -> None:
        if self._rebuild_timer is not None:
            self._rebuild_timer.stop()
        self._rebuild_timer = self.set_timer(0.12, self._flush_rebuild, name="encode-rebuild")

    def _flush_rebuild(self) -> None:
        self._rebuild_timer = None
        if not self.is_mounted:
            return
        self._rebuild_config()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "paper-select":
            self._paper_size = str(event.value)
        self._rebuild_config()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-encode":
            self.query_one("#btn-encode", Button).disabled = True
            self._set_progress(0, "Encoding…", False)
            self._run_encode()
        elif event.button.id == "input-file-browse":
            from cli.tui.file_picker import FilePickerScreen
            self.app.push_screen(FilePickerScreen(mode="file"), callback=self._on_file_picked)
        elif event.button.id == "enc-config-browse":
            from cli.tui.file_picker import FilePickerScreen
            self.app.push_screen(FilePickerScreen(mode="file"), callback=self._on_config_picked)

    def _on_config_picked(self, result: Path | None) -> None:
        if result is None:
            return
        self.query_one("#enc-config-path", Input).value = str(result)
        self._rebuild_config()

    def _on_file_picked(self, result: Path | None) -> None:
        if result is None:
            return
        self._input_path = result
        self.query_one("#input-file-label", Static).update(str(result))
        self._rebuild_config()

    def _rebuild_config(self) -> None:
        info = self.query_one("#encode-info-display", Static)
        try:
            base = tui_encoding_config(
                self.query_one("#enc-config-path", Input).value,
                self.query_one("#enc-num-colors", Input).value,
                self.query_one("#enc-cell-size", Input).value,
                self._paper_size,
                self.query_one("#enc-print-dpi", Input).value,
                self.query_one("#enc-rs", Input).value,
                self.query_one("#enc-red-pages", Input).value,
                self.query_one("#enc-margin-t", Input).value,
                self.query_one("#enc-margin-r", Input).value,
                self.query_one("#enc-margin-b", Input).value,
                self.query_one("#enc-margin-l", Input).value,
            )
            self._config = config_with_page_dimensions(base, self._paper_size)
            info.update(format_encoding_info_panel(self._config, self._paper_size))
        except Exception as e:
            self._config = None
            info.update(f"[red]{e}[/red]")
        self._update_plan()

    def _update_plan(self) -> None:
        plan = self.query_one("#encoding-plan", Static)
        btn = self.query_one("#btn-encode", Button)
        if not self._config or not self._input_path:
            plan.update("[dim]Set encoding parameters and select an input file[/dim]")
            btn.disabled = True
            return
        plan.update(format_encoding_plan(self._config, self._input_path))
        btn.disabled = False

    @work(thread=True)
    def _run_encode(self) -> None:
        try:
            from common.config import FLAG_ENCRYPTED

            config, input_path, passphrase = self._config, self._input_path, self._passphrase
            if config is None or input_path is None:
                raise ValueError("Invalid configuration")
            flags = FLAG_ENCRYPTED if passphrase else 0
            file_size = input_path.stat().st_size
            total_pages = max(1, -(-file_size // data_capacity_bytes(config)))
            config_dict = {k: getattr(config, k) for k in ALGO_FIELDS}
            for k in (
                "margin_top_mm",
                "margin_right_mm",
                "margin_bottom_mm",
                "margin_left_mm",
            ):
                config_dict[k] = getattr(config, k)
            job_dir = create_job(input_path.name, "inline", config_dict, total_pages)
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
