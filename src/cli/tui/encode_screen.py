from __future__ import annotations

from functools import partial
from pathlib import Path

from textual import work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.timer import Timer
from textual.widget import Widget
from textual.widgets import Button, Input, Label, ProgressBar, Static

from cli.tui.encode_pick_state import apply_encode_pick, refresh_encode_pick_labels
from cli.tui.encode_pickers import encode_option_picker
from cli.tui.encode_screen_actions import rebuild_encode_screen, run_encode_job
from cli.tui.encoding_form import EncodingFormPicks, apply_profile_picks, default_encoding_form_picks
from cli.tui.encoding_settings_panel import EncodingSettingsPanel
from cli.tui.file_picker import FilePickerScreen
from cli.tui.nav_messages import OpenPanel
from common.config import PaperClipConfig


class EncodeScreen(Widget):

    def __init__(self) -> None:
        super().__init__()
        self._config: PaperClipConfig | None = None
        self._picks: EncodingFormPicks = default_encoding_form_picks()
        self._input_path: Path | None = None
        self._passphrase: str | None = None
        self._rebuild_timer: Timer | None = None
        self.last_job_id: str | None = None

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
                    yield Button("Print this job", id="btn-encode-print", disabled=True, compact=True)
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
        elif bid == "btn-encode-print" and self.last_job_id:
            self.post_message(OpenPanel("nav-print", self.last_job_id))
        elif bid == "enc-use-profile":
            apply_profile_picks(self._picks)
            refresh_encode_pick_labels(self, self._picks)
            self._rebuild_config()
        elif picker := encode_option_picker(bid):
            self.app.push_screen(picker, callback=partial(self._apply_picker_choice, bid))

    def _apply_picker_choice(self, button_id: str, result: object | None) -> None:
        if result is None or not apply_encode_pick(self._picks, button_id, result):
            return
        refresh_encode_pick_labels(self, self._picks)
        self._rebuild_config()

    def _on_file_picked(self, result: Path | None) -> None:
        if result is None:
            return
        self._input_path = result
        self.query_one("#input-file-label", Static).update(str(result))
        self._rebuild_config()

    def _rebuild_config(self) -> None:
        rebuild_encode_screen(self)

    @work(thread=True)
    def _run_encode(self) -> None:
        run_encode_job(self)
