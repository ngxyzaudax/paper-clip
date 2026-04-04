from pathlib import Path

from textual import work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widget import Widget
from textual.widgets import Button, Input, Label, ProgressBar, Select, Static

from common.image_resolver import SUPPORTED_IMAGE_EXTS, is_image_file
from serialization.decode.pipeline import decode


class DecodeScreen(Widget):

    def __init__(self) -> None:
        super().__init__()
        self._source_path: Path | None = None
        self._passphrase: str | None = None
        self._save_pw_label_snapshot: str = ""
        self._classifier_snapshot: str = "auto"

    def compose(self) -> ComposeResult:
        with VerticalScroll(classes="form-container"):
            yield Static("Decode Pages to File", classes="screen-title")
            yield Static("Configuration is read from page headers automatically", classes="note")
            with Vertical(classes="section"):
                yield Static("Source", classes="section-title")
                yield Label("Input (PNG/image file or folder of scanned pages)")
                with Horizontal(classes="picker-row"):
                    yield Static("[dim]No source selected[/dim]", id="source-label")
                    yield Button("File...", id="source-file-browse")
                    yield Button("Folder...", id="source-dir-browse")
                yield Static("", id="source-info", classes="details-panel")
            with Vertical(classes="section"):
                yield Static("Options", classes="section-title")
                with Horizontal(classes="form-row"):
                    with Vertical(classes="form-col"):
                        yield Label("Classifier")
                        yield Select(
                            [("Auto (ML if available)", "auto"), ("ML Model", "ml"), ("RGB fallback", "rgb")],
                            value="auto", id="classifier-select",
                        )
                    with Vertical(classes="form-col"):
                        yield Label("Password")
                        yield Input(placeholder="decryption password", password=True, id="password-input")
                yield Label("Save password in keystore as (optional)")
                yield Input(placeholder="label, after successful decode", id="save-pw-label")
                yield Label("Output File")
                yield Input(value="./decoded_output", id="output-file")
            with Horizontal(classes="button-bar"):
                yield Button("Decode", variant="primary", id="btn-decode", disabled=True)
            yield ProgressBar(id="progress")
            yield Static("", id="status")

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "password-input":
            self._passphrase = event.value or None

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-decode":
            self._start_decode()
        elif event.button.id == "source-file-browse":
            self._browse_source("file")
        elif event.button.id == "source-dir-browse":
            self._browse_source("directory")

    def _browse_source(self, mode: str) -> None:
        from cli.tui.file_picker import FilePickerScreen
        self.app.push_screen(
            FilePickerScreen(mode=mode, title="Select scan source"),
            callback=self._on_source_picked,
        )

    def _on_source_picked(self, result: Path | None) -> None:
        if result is None:
            return
        self._validate_source(result)

    def _validate_source(self, path: Path) -> None:
        info_widget = self.query_one("#source-info", Static)
        btn = self.query_one("#btn-decode", Button)
        label = self.query_one("#source-label", Static)

        if is_image_file(path):
            self._source_path = path
            label.update(str(path))
            info_widget.update(f"[green]Image file:[/green] {path.name}")
            btn.disabled = False
            return

        if path.is_dir():
            image_files: list[Path] = []
            for ext in SUPPORTED_IMAGE_EXTS:
                image_files.extend(path.glob(f"*{ext}"))
            image_files = sorted(image_files)
            if image_files:
                self._source_path = path
                label.update(str(path))
                listing = "\n".join(f"  {f.name}" for f in image_files[:8])
                if len(image_files) > 8:
                    listing += f"\n  ... and {len(image_files) - 8} more"
                info_widget.update(f"[green]Found {len(image_files)} page(s):[/green]\n{listing}")
                btn.disabled = False
                return
            info_widget.update("[yellow]No image files found in directory[/yellow]")

        self._source_path = None
        label.update("[dim]No source selected[/dim]")
        info_widget.update("[dim]Select a PNG/image file or directory of scanned pages[/dim]")
        btn.disabled = True

    def _start_decode(self) -> None:
        self._save_pw_label_snapshot = self.query_one("#save-pw-label", Input).value.strip()
        cv = self.query_one("#classifier-select", Select).value
        self._classifier_snapshot = str(cv) if cv != Select.BLANK else "auto"
        self._output_path = Path(self.query_one("#output-file", Input).value).expanduser()
        self.query_one("#btn-decode", Button).disabled = True
        self.query_one("#status", Static).update("[bold]Decoding...[/bold]")
        self._run_decode()

    @work(thread=True)
    def _run_decode(self) -> None:
        source = self._source_path
        output_path = self._output_path

        def on_page(idx: int, total: int, path: Path | None) -> None:
            self.app.call_from_thread(self._set_progress, idx + 1, total)

        save_lbl = self._save_pw_label_snapshot

        try:
            result, original_filename = decode(
                source, output_path, on_page_decoded=on_page,
                passphrase=self._passphrase, classifier=self._classifier_snapshot,
            )
            final_path = output_path.parent / original_filename if original_filename else output_path
            done_msg = (
                f"[bold green]Decoded {len(result):,} bytes to {final_path}\n"
                f"Original filename: {original_filename or 'unknown'}\n"
                f"SHA-256 integrity verified[/bold green]"
            )
            if save_lbl and self._passphrase:
                from common.keystore import save_password as store_pw
                store_pw(save_lbl, self._passphrase)
                done_msg += f"\n[cyan]Password saved as '{save_lbl}'[/cyan]"
            self.app.call_from_thread(self._on_done, done_msg, True)
        except Exception as e:
            self.app.call_from_thread(self._on_done, f"[bold red]Error: {e}[/bold red]", False)

    def _set_progress(self, current: int, total: int) -> None:
        self.query_one("#progress", ProgressBar).update(total=total, progress=current)
        self.query_one("#status", Static).update(f"Decoding page {current}/{total}")

    def _on_done(self, message: str, success: bool = True) -> None:
        if success:
            self.query_one("#progress", ProgressBar).update(total=100, progress=100)
        self.query_one("#status", Static).update(message)
        self.query_one("#btn-decode", Button).disabled = False
