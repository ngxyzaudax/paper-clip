from pathlib import Path

from textual import work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widget import Widget
from textual.widgets import Button, Input, Label, ProgressBar, Select, Static

from cli.generate_cmd import create_test_data_job
from common.config_store import list_profiles


class GenerateScreen(Widget):

    def __init__(self) -> None:
        super().__init__()
        self._snap_profile: str = ""
        self._snap_pages: int = 1
        self._snap_pw: str | None = None

    def compose(self) -> ComposeResult:
        prof_opts = [(n, n) for n, _ in list_profiles()]
        with VerticalScroll(classes="form-container"):
            yield Static("Generate Test Job", classes="screen-title")
            yield Static(
                "[dim]Random payload sized to fill page(s), encoded into data/jobs/ (no print or scan).[/dim]",
                classes="note",
            )
            with Vertical(classes="section"):
                yield Static("Parameters", classes="section-title")
                with Horizontal(classes="form-row"):
                    with Vertical(classes="form-col"):
                        yield Label("Profile")
                        yield Select(prof_opts, prompt="Select profile", id="profile-select")
                    with Vertical(classes="form-col"):
                        yield Label("Pages")
                        yield Input(value="1", id="pages-input")
                yield Label("Password (optional)")
                yield Input(placeholder="encryption password", password=True, id="password-input")
            with Horizontal(classes="button-bar"):
                yield Button("Generate", variant="primary", id="btn-generate", disabled=True)
            yield ProgressBar(id="progress")
            yield Static("", id="status")

    def on_select_changed(self, event: Select.Changed) -> None:
        self._check_ready()

    def on_input_changed(self, event: Input.Changed) -> None:
        self._check_ready()

    def _check_ready(self) -> None:
        ok = self.query_one("#profile-select", Select).value != Select.BLANK
        self.query_one("#btn-generate", Button).disabled = not ok

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-generate":
            self._snap_profile = str(self.query_one("#profile-select", Select).value)
            self._snap_pages = int(self.query_one("#pages-input", Input).value or "1")
            v = self.query_one("#password-input", Input).value
            self._snap_pw = v or None
            self.query_one("#btn-generate", Button).disabled = True
            self._run_generate()

    @work(thread=True)
    def _run_generate(self) -> None:
        try:

            def on_page(idx: int, total: int, path: Path | None) -> None:
                pct = ((idx + 1) / total) * 100
                self.app.call_from_thread(self._prog, pct, f"Page {idx + 1}/{total}")

            job_dir, png_paths, test_path, sha256 = create_test_data_job(
                self._snap_profile, self._snap_pages, self._snap_pw, on_page_complete=on_page,
            )
            listing = "\n".join(p.name for p in png_paths)
            msg = (
                f"[bold green]Job: {job_dir}[/bold green]\n"
                f"Test file: {test_path}\nSHA-256: {sha256}\n\n{listing}"
            )
        except Exception as e:
            msg = f"[bold red]Error: {e}[/bold red]"
        self.app.call_from_thread(self._done, msg)

    def _prog(self, pct: float, label: str) -> None:
        self.query_one("#progress", ProgressBar).update(total=100, progress=pct)
        self.query_one("#status", Static).update(label)

    def _done(self, msg: str) -> None:
        self.query_one("#progress", ProgressBar).update(total=100, progress=100)
        self.query_one("#status", Static).update(msg)
        self.query_one("#btn-generate", Button).disabled = False
