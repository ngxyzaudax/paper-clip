from pathlib import Path

from textual import work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widget import Widget
from textual.widgets import Button, Checkbox, Input, Label, ProgressBar, Select, Static

from cli.print_cmd import run_print_job
from common.cups_client import list_printers


class PrintScreen(Widget):

    def __init__(self) -> None:
        super().__init__()
        self._files: list[Path] = []
        self._print_files_snap: list[Path] = []
        self._print_printer_snap: str | None = None
        self._print_res_snap: str | None = None
        self._print_paper_snap: str | None = None
        self._print_color_snap: str | None = None
        self._print_duplex_snap: str | None = None
        self._print_save_snap: bool = False

    def compose(self) -> ComposeResult:
        with VerticalScroll(classes="form-container"):
            yield Static("Print PNG Pages", classes="screen-title")
            with Vertical(classes="section"):
                yield Static("Files", classes="section-title")
                yield Static("[dim]No files added[/dim]", id="file-list")
                with Horizontal(classes="picker-row"):
                    yield Button("Add PNG...", id="btn-add-file")
                    yield Button("Clear list", id="btn-clear-files")
            with Vertical(classes="section"):
                yield Static("Printer", classes="section-title")
                yield Select([], prompt="Loading printers...", id="printer-select")
                yield Label("Resolution (optional, e.g. 600dpi)")
                yield Input(placeholder="default from printer", id="resolution-input")
                yield Label("Paper size (optional)")
                yield Input(placeholder="e.g. A4", id="paper-input")
                yield Label("Color mode (optional)")
                yield Input(placeholder="RGB, Gray, ...", id="color-input")
                yield Label("Duplex (optional)")
                yield Input(placeholder="None, DuplexNoTumble, ...", id="duplex-input")
                yield Checkbox("Save selected printer as default", id="chk-save-default")
            with Horizontal(classes="button-bar"):
                yield Button("Print", variant="primary", id="btn-print", disabled=True)
            yield ProgressBar(id="progress")
            yield Static("", id="status")

    def on_mount(self) -> None:
        printers = list_printers()
        opts = [(p.name, p.name) for p in printers]
        sel = self.query_one("#printer-select", Select)
        sel.set_options(opts)
        if opts:
            sel.value = opts[0][1]
        else:
            self.query_one("#status", Static).update("[yellow]No printers found[/yellow]")

    def on_select_changed(self, event: Select.Changed) -> None:
        self._check_ready()

    def _check_ready(self) -> None:
        has_pr = self.query_one("#printer-select", Select).value != Select.BLANK
        self.query_one("#btn-print", Button).disabled = not (self._files and has_pr)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-add-file":
            from cli.tui.file_picker import FilePickerScreen
            self.app.push_screen(FilePickerScreen(mode="file"), callback=self._on_file)
        elif event.button.id == "btn-clear-files":
            self._files.clear()
            self._update_file_list()
            self._check_ready()
        elif event.button.id == "btn-print":
            pr_val = self.query_one("#printer-select", Select).value
            self._print_printer_snap = str(pr_val) if pr_val != Select.BLANK else None
            self._print_res_snap = self.query_one("#resolution-input", Input).value.strip() or None
            self._print_paper_snap = self.query_one("#paper-input", Input).value.strip() or None
            self._print_color_snap = self.query_one("#color-input", Input).value.strip() or None
            self._print_duplex_snap = self.query_one("#duplex-input", Input).value.strip() or None
            self._print_save_snap = self.query_one("#chk-save-default", Checkbox).value
            self._print_files_snap = list(self._files)
            self.query_one("#btn-print", Button).disabled = True
            self._run_print()

    def _on_file(self, result: Path | None) -> None:
        if result is None:
            return
        self._files.append(result)
        self._update_file_list()
        self._check_ready()

    def _update_file_list(self) -> None:
        w = self.query_one("#file-list", Static)
        if not self._files:
            w.update("[dim]No files added[/dim]")
            return
        w.update("\n".join(str(p) for p in self._files))

    @work(thread=True)
    def _run_print(self) -> None:
        try:
            err, _pn, results = run_print_job(
                self._print_files_snap,
                self._print_printer_snap,
                self._print_res_snap,
                self._print_paper_snap,
                self._print_color_snap,
                self._print_duplex_snap,
                self._print_save_snap,
            )
            if err:
                msg = f"[bold red]{err}[/bold red]"
            else:
                lines = [f"[green]{n}[/green] job {jid}" for n, jid in results]
                msg = "[bold green]Submitted:[/bold green]\n" + "\n".join(lines)
        except Exception as e:
            msg = f"[bold red]{e}[/bold red]"
        self.app.call_from_thread(self._done, msg)

    def _done(self, msg: str) -> None:
        self.query_one("#progress", ProgressBar).update(total=100, progress=100)
        self.query_one("#status", Static).update(msg)
        self.query_one("#btn-print", Button).disabled = False
