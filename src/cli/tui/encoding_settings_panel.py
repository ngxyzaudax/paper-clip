from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widget import Widget
from textual.widgets import Button, Input, Label, Static

from cli.tui.encoding_form import EncodingFormPicks, EncodingFormTextInputs
from common.cell_size_picks import cell_size_pick_label
from common.color_picker import symbol_option_label
from common.dot_print_picks import dot_gain_pick_label, dot_guard_pick_label
from common.paper_sizes import paper_size_option_label
from common.print_dpi_presets import print_dpi_option_label


class EncodingSettingsPanel(Widget):

    def __init__(self, picks: EncodingFormPicks, text_defaults: EncodingFormTextInputs) -> None:
        super().__init__()
        self._picks = picks
        self._tx = text_defaults

    def compose(self) -> ComposeResult:
        yield Static("Encoding settings", classes="encode-panel-title")
        with Vertical(classes="section"):
            with VerticalScroll(classes="encode-form-scroll"):
                with Horizontal(classes="form-row"):
                    with Vertical(classes="form-col"):
                        yield Label("Symbols")
                        yield Button(
                            symbol_option_label(self._picks.symbol_count),
                            id="enc-symbols-pick",
                            compact=True,
                        )
                    with Vertical(classes="form-col"):
                        yield Label("Cell px")
                        yield Button(
                            cell_size_pick_label(self._picks.cell_size_px),
                            id="enc-cell-pick",
                            compact=True,
                        )
                with Horizontal(classes="form-row"):
                    with Vertical(classes="form-col"):
                        yield Label("Print DPI")
                        yield Button(
                            print_dpi_option_label(self._picks.print_dpi),
                            id="enc-dpi-pick",
                            compact=True,
                        )
                    with Vertical(classes="form-col"):
                        yield Label("RS redundancy")
                        yield Input(value=self._tx.rs_redundancy, id="enc-rs", compact=True)
                with Horizontal(classes="form-row"):
                    with Vertical(classes="form-col"):
                        yield Label("Parity pages")
                        yield Input(value=self._tx.redundancy_pages, id="enc-red-pages", compact=True)
                with Horizontal(classes="form-row"):
                    with Vertical(classes="form-col"):
                        yield Label("Dot gain")
                        yield Button(
                            dot_gain_pick_label(self._picks.dot_gain_factor),
                            id="enc-dot-gain-pick",
                            compact=True,
                        )
                    with Vertical(classes="form-col"):
                        yield Label("Dot guard px")
                        yield Button(
                            dot_guard_pick_label(self._picks.dot_guard_band_px),
                            id="enc-dot-guard-pick",
                            compact=True,
                        )
                with Horizontal(classes="form-row"):
                    yield Label("Margins mm")
                with Horizontal(classes="form-row"):
                    with Vertical(classes="form-col"):
                        yield Label("Top")
                        yield Input(value=self._tx.margin_top_mm, id="enc-margin-t", compact=True)
                    with Vertical(classes="form-col"):
                        yield Label("Right")
                        yield Input(value=self._tx.margin_right_mm, id="enc-margin-r", compact=True)
                    with Vertical(classes="form-col"):
                        yield Label("Bottom")
                        yield Input(value=self._tx.margin_bottom_mm, id="enc-margin-b", compact=True)
                    with Vertical(classes="form-col"):
                        yield Label("Left")
                        yield Input(value=self._tx.margin_left_mm, id="enc-margin-l", compact=True)
                with Horizontal(classes="form-row"):
                    with Vertical(classes="form-col"):
                        yield Label("Paper size")
                        yield Button(
                            paper_size_option_label(self._picks.paper_size),
                            id="enc-paper-pick",
                            compact=True,
                        )
