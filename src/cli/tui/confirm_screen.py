from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import CenterMiddle, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static


class ConfirmScreen(ModalScreen[bool]):
    """Modal yes/no prompt for actions that print, save, or move files."""

    DEFAULT_CSS = """
    ConfirmScreen #confirm-panel {
        width: 72;
        height: auto;
        max-height: 90%;
        border: heavy $warning;
        background: $surface;
        padding: 1 2;
    }
    ConfirmScreen #confirm-title {
        text-style: bold;
        color: $warning;
        margin-bottom: 1;
    }
    ConfirmScreen #confirm-body {
        margin-bottom: 1;
    }
    ConfirmScreen #confirm-buttons {
        height: auto;
        align: right middle;
    }
    ConfirmScreen #confirm-buttons Button {
        margin-left: 1;
        min-width: 12;
    }
    """

    BINDINGS = [Binding("escape", "cancel", "Cancel"), Binding("enter", "confirm", "Confirm")]

    def __init__(self, title: str, body: str, confirm_label: str = "Confirm") -> None:
        super().__init__()
        self._title = title
        self._body = body
        self._confirm_label = confirm_label

    def compose(self) -> ComposeResult:
        with CenterMiddle():
            with Vertical(id="confirm-panel"):
                yield Static(self._title, id="confirm-title")
                yield Static(self._body, id="confirm-body", markup=False)
                with Horizontal(id="confirm-buttons"):
                    yield Button("Cancel", id="confirm-cancel", compact=True)
                    yield Button(self._confirm_label, id="confirm-ok", variant="warning", compact=True)

    def on_mount(self) -> None:
        self.query_one("#confirm-cancel", Button).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "confirm-ok")

    def action_cancel(self) -> None:
        self.dismiss(False)

    def action_confirm(self) -> None:
        self.dismiss(True)
