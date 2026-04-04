from pathlib import Path
from typing import Literal

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, DirectoryTree, Static


PickerMode = Literal["file", "directory"]


class FilteredTree(DirectoryTree):
    def filter_paths(self, paths: "Iterable[Path]") -> "Iterable[Path]":
        return sorted(
            (p for p in paths if not p.name.startswith(".")),
            key=lambda p: (not p.is_dir(), p.name.lower()),
        )


class FilePickerScreen(ModalScreen[Path | None]):
    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def __init__(
        self,
        start_path: Path | None = None,
        mode: PickerMode = "file",
        title: str | None = None,
    ) -> None:
        super().__init__()
        self._start = start_path or Path.home()
        self._mode = mode
        self._title = title or ("Select File" if mode == "file" else "Select Directory")
        self._selected: Path | None = None

    def compose(self) -> ComposeResult:
        with Vertical(id="picker-modal"):
            yield Static(self._title, id="picker-title")
            yield Static("[dim]No selection[/dim]", id="picker-selection")
            yield FilteredTree(str(self._start), id="picker-tree")
            with Horizontal(id="picker-buttons"):
                yield Button("Select", variant="primary", id="picker-select", disabled=True, compact=True)
                yield Button("Cancel", id="picker-cancel", compact=True)

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        if self._mode == "file":
            self._selected = event.path
            self.query_one("#picker-selection", Static).update(str(event.path))
            self.query_one("#picker-select", Button).disabled = False

    def on_directory_tree_directory_selected(self, event: DirectoryTree.DirectorySelected) -> None:
        if self._mode == "directory":
            self._selected = event.path
            self.query_one("#picker-selection", Static).update(str(event.path))
            self.query_one("#picker-select", Button).disabled = False

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "picker-select":
            self.dismiss(self._selected)
        elif event.button.id == "picker-cancel":
            self.dismiss(None)

    def action_cancel(self) -> None:
        self.dismiss(None)
