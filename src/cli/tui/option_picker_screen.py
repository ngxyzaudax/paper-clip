from __future__ import annotations

from typing import Any

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import CenterMiddle, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Static


class OptionPickerScreen(ModalScreen[Any | None]):

    DEFAULT_CSS = """
    OptionPickerScreen #option-picker-panel {
        width: 56;
        height: auto;
        max-height: 24;
        border: heavy $primary;
        background: $surface;
        padding: 1 2;
    }
    OptionPickerScreen #option-picker-title {
        text-align: left !important;
        margin-bottom: 1;
    }
    OptionPickerScreen #option-picker-scroll {
        max-height: 18;
        height: auto;
    }
    OptionPickerScreen .option-picker-choice {
        width: 100%;
        min-height: 1;
    }
    OptionPickerScreen #option-picker-cancel {
        margin-top: 1;
        width: 100%;
    }
    """

    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def __init__(self, title: str, options: list[tuple[str, Any]]) -> None:
        super().__init__()
        self._title = title
        self._options = options

    def compose(self) -> ComposeResult:
        with CenterMiddle():
            with Vertical(id="option-picker-panel"):
                yield Static(self._title, id="option-picker-title")
                with VerticalScroll(id="option-picker-scroll"):
                    for i, (label, _value) in enumerate(self._options):
                        yield Button(
                            label,
                            id=f"opti-{i}",
                            classes="option-picker-choice",
                            compact=True,
                        )
                yield Button("Cancel", id="option-picker-cancel", compact=True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""
        if bid == "option-picker-cancel":
            self.dismiss(None)
            return
        if bid.startswith("opti-"):
            idx = int(bid[5:])
            self.dismiss(self._options[idx][1])

    def action_cancel(self) -> None:
        self.dismiss(None)
