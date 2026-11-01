from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widget import Widget
from textual.widgets import Button, Input, Label, Static

from cli.tui.encode_pick_fields import PickField, field_rows
from cli.tui.encoding_form import EncodingFormPicks, profile_source_text


class EncodingSettingsPanel(Widget):

    def __init__(self, picks: EncodingFormPicks) -> None:
        super().__init__()
        self._picks = picks

    def compose(self) -> ComposeResult:
        yield Static("Encoding settings", classes="encode-panel-title")
        yield Static(profile_source_text(self._picks), id="enc-profile-source")
        with Vertical(classes="section"):
            with VerticalScroll(classes="encode-form-scroll"):
                for row in field_rows():
                    with Horizontal(classes="form-row"):
                        for field in row:
                            yield from self._pick_column(field)
                with Horizontal(classes="form-row"):
                    with Vertical(classes="form-col"):
                        yield Label("Margins mm")
                        yield Input(value=f"{self._picks.margin_mm:g}", id="enc-margin-input", compact=True)
                    with Vertical(classes="form-col"):
                        yield Label("Density")
                        yield Button("Reset to profile", id="enc-use-profile", compact=True)

    def _pick_column(self, field: PickField) -> ComposeResult:
        with Vertical(classes="form-col"):
            yield Label(field.label)
            yield Button(field.describe(getattr(self._picks, field.attribute)), id=field.button_id, compact=True)
