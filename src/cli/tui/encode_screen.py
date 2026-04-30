from __future__ import annotations

import logging
from functools import partial
from pathlib import Path

from textual import work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.timer import Timer
from textual.widget import Widget
from textual.widgets import Button, Input, Label, ProgressBar, Static

from cli.tui.encode_execution import format_encode_success_message, run_tui_encode_job
from cli.tui.encode_pickers import encode_option_picker
from cli.tui.encoding_form import (
    EncodingFormPicks,
    default_encoding_form_picks,
    resolve_encoding_form,
)
from cli.tui.encoding_settings_panel import EncodingSettingsPanel
from cli.tui.encode_helpers import format_encoding_info_panel, format_encoding_plan
from common.perf import log_phase
from cli.tui.file_picker import FilePickerScreen
from common.cell_size_picks import cell_size_pick_label
from common.color_picker import symbol_option_label
from common.config import PaperClipConfig
from common.paper_sizes import config_with_page_dimensions, paper_size_option_label
from common.print_dpi_presets import print_dpi_option_label
from common.parity_pages_picks import parity_pages_option_label
from common.rs_redundancy_picks import rs_redundancy_option_label


class EncodeScreen(Widget):

    def __init__(self) -> None:
        super().__init__()
        self._config: PaperClipConfig | None = None
        self._picks: EncodingFormPicks = default_encoding_form_picks()
        self._input_path: Path | None = None
        self._passphrase: str | None = None
        self._rebuild_timer: Timer | None = None

    def compose(self) -> ComposeResult:
        with Vertical(classes="encode-screen-layout form-container"):
            with Horizontal(classes="encode-split"):
                with Vertical(classes="encode-form-col"):
                    yield EncodingSettingsPanel(self._picks)
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
                            placeholder="optional; replaces default encryption key",
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
        if event.input.id == "enc-margin-input":
            try:
                self._picks.margin_mm = float(event.value)
            except ValueError:
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

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "btn-encode":
            self.query_one("#btn-encode", Button).disabled = True
            self._set_progress(0, "Encoding…", False)
            self._run_encode()
        elif bid == "input-file-browse":
            self.app.push_screen(FilePickerScreen(mode="file"), callback=self._on_file_picked)
        elif picker := encode_option_picker(bid):
            self.app.push_screen(picker, callback=partial(self._apply_picker_choice, bid))

    def _apply_picker_choice(self, button_id: str, result: object | None) -> None:
        if result is None:
            return
        match button_id:
            case "enc-cell-pick":
                self._picks.cell_size_px = int(result)
            case "enc-symbols-pick":
                self._picks.symbol_count = int(result)
            case "enc-dpi-pick":
                self._picks.print_dpi = int(result)
            case "enc-rs-pick":
                self._picks.rs_redundancy = float(result)
            case "enc-parity-pick":
                self._picks.redundancy_pages = int(result)
            case "enc-paper-pick":
                self._picks.paper_size = str(result)
            case _:
                return
        self._refresh_pick_button_labels()
        self._rebuild_config()

    def _refresh_pick_button_labels(self) -> None:
        self.query_one("#enc-symbols-pick", Button).label = symbol_option_label(self._picks.symbol_count)
        self.query_one("#enc-cell-pick", Button).label = cell_size_pick_label(self._picks.cell_size_px)
        self.query_one("#enc-dpi-pick", Button).label = print_dpi_option_label(self._picks.print_dpi)
        self.query_one("#enc-rs-pick", Button).label = rs_redundancy_option_label(self._picks.rs_redundancy)
        self.query_one("#enc-parity-pick", Button).label = parity_pages_option_label(
            self._picks.redundancy_pages,
        )
        self.query_one("#enc-paper-pick", Button).label = paper_size_option_label(self._picks.paper_size)

    def _on_file_picked(self, result: Path | None) -> None:
        if result is None:
            return
        self._input_path = result
        self.query_one("#input-file-label", Static).update(str(result))
        self._rebuild_config()

    def _rebuild_config(self) -> None:
        logger = logging.getLogger(__name__)
        info = self.query_one("#encode-info-display", Static)
        try:
            with log_phase(logger, "tui.EncodeScreen.resolve_form"):
                base = resolve_encoding_form(self._picks)
                self._config = config_with_page_dimensions(base, self._picks.paper_size)
            with log_phase(logger, "tui.EncodeScreen.update_info_display"):
                info.update(format_encoding_info_panel(self._config, self._picks.paper_size))
        except Exception as e:
            self._config = None
            info.update(f"[red]{e}[/red]")
        with log_phase(logger, "tui.EncodeScreen.update_encoding_plan"):
            self._update_plan()

    def _update_plan(self) -> None:
        plan = self.query_one("#encoding-plan", Static)
        btn = self.query_one("#btn-encode", Button)
        if not self._config or not self._input_path:
            plan.update("[dim]Set encoding parameters and select an input file[/dim]")
            btn.disabled = True
            return
        plan.update(
            format_encoding_plan(self._config, self._input_path, self._passphrase),
        )
        btn.disabled = False

    @work(thread=True)
    def _run_encode(self) -> None:
        try:
            config, input_path, passphrase = self._config, self._input_path, self._passphrase
            if config is None or input_path is None:
                raise ValueError("Invalid configuration")

            def on_page(idx: int, total: int, path: Path | None) -> None:
                self.app.call_from_thread(
                    self._set_progress,
                    ((idx + 1) / total) * 100,
                    f"Page {idx+1}/{total}",
                )

            job_dir, png_paths = run_tui_encode_job(
                config=config,
                input_path=input_path,
                passphrase=passphrase,
                on_page_complete=on_page,
            )
            msg = format_encode_success_message(job_dir, png_paths)
        except Exception as e:
            msg = f"[bold red]Error: {e}[/bold red]"
        self.app.call_from_thread(self._set_progress, 100, msg, True)

    def _set_progress(self, pct: float, msg: str, done: bool = False) -> None:
        self.query_one("#progress", ProgressBar).update(total=100, progress=100 if done else pct)
        self.query_one("#status", Static).update(msg)
        if done:
            self.query_one("#btn-encode", Button).disabled = False
