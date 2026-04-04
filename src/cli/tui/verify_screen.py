import tempfile
from pathlib import Path

import numpy as np
from textual import work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widget import Widget
from textual.widgets import Button, Label, ProgressBar, Select, Static

from common.config import PaperClipConfig
from common.config_store import list_profiles, load_profile
from common.paper_sizes import DEFAULT_PAPER_SIZE, paper_size_dimensions, paper_size_options
from serialization.decode.pipeline import decode
from serialization.encode.pipeline import render_pages


class VerifyScreen(Widget):

    def __init__(self) -> None:
        super().__init__()
        self._config: PaperClipConfig | None = None
        self._paper_size: str = DEFAULT_PAPER_SIZE
        self._test_path: Path | None = None

    def compose(self) -> ComposeResult:
        profiles = list_profiles()
        options = [(name, name) for name, _ in profiles]
        with VerticalScroll(classes="form-container"):
            yield Static("Roundtrip Verification", classes="screen-title")
            with Vertical(classes="section"):
                yield Static("Configuration", classes="section-title")
                with Horizontal(classes="form-row"):
                    with Vertical(classes="form-col"):
                        yield Label("Profile")
                        yield Select(options, prompt="Select profile", id="config-select")
                    with Vertical(classes="form-col"):
                        yield Label("Paper Size")
                        yield Select(paper_size_options(), value=DEFAULT_PAPER_SIZE, id="paper-select")
            with Vertical(classes="section"):
                yield Static("Test File", classes="section-title")
                with Horizontal(classes="picker-row"):
                    yield Static("[dim]No file selected[/dim]", id="test-file-label")
                    yield Button("Browse...", id="test-file-browse")
            with Horizontal(classes="button-bar"):
                yield Button("Verify", variant="primary", id="btn-verify", disabled=True)
            yield ProgressBar(id="progress")
            yield Static("", id="status")

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.value == Select.BLANK:
            return
        if event.select.id == "config-select":
            try:
                self._config = load_profile(str(event.value))
                self._apply_paper_size()
            except Exception as e:
                self._config = None
                self.query_one("#status", Static).update(f"[red]{e}[/red]")
        elif event.select.id == "paper-select":
            self._paper_size = str(event.value)
            self._apply_paper_size()
        self._check_ready()

    def _apply_paper_size(self) -> None:
        if not self._config:
            return
        from dataclasses import replace
        try:
            w, h = paper_size_dimensions(self._paper_size)
            self._config = replace(self._config, page_width_mm=w, page_height_mm=h)
        except ValueError:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-verify":
            self._verify_config = self._config
            self.query_one("#btn-verify", Button).disabled = True
            self.query_one("#status", Static).update("[bold]Running verification...[/bold]")
            self._run_verify()
        elif event.button.id == "test-file-browse":
            from cli.tui.file_picker import FilePickerScreen
            self.app.push_screen(FilePickerScreen(mode="file"), callback=self._on_file_picked)

    def _on_file_picked(self, result: Path | None) -> None:
        if result is None:
            return
        self._test_path = result
        self.query_one("#test-file-label", Static).update(str(result))
        self._check_ready()

    def _check_ready(self) -> None:
        ready = self._config is not None and self._test_path is not None and self._test_path.is_file()
        self.query_one("#btn-verify", Button).disabled = not ready

    @work(thread=True)
    def _run_verify(self) -> None:
        try:
            input_path = self._test_path
            config = self._verify_config
            original = input_path.read_bytes()

            def on_enc(idx: int, total: int, path: Path | None) -> None:
                pct = ((idx + 1) / total) * 50
                self.app.call_from_thread(self._set_progress, pct, f"Rendering page {idx + 1}/{total}")

            pil_images = render_pages(input_path, config, on_page_complete=on_enc)
            bgr_images = [np.array(img.convert("RGB"))[:, :, ::-1] for img in pil_images]

            def on_dec(idx: int, total: int, path: Path | None) -> None:
                pct = 50 + ((idx + 1) / total) * 50
                self.app.call_from_thread(self._set_progress, pct, f"Decoding page {idx + 1}/{total}")

            with tempfile.TemporaryDirectory() as tmpdir:
                try:
                    recovered, _ = decode(bgr_images, Path(tmpdir) / "decoded", on_page_decoded=on_dec)
                except Exception:
                    recovered = b""

            self.app.call_from_thread(self._show_results, original, recovered, len(pil_images))
        except Exception as e:
            self.app.call_from_thread(self._show_error, str(e))

    def _set_progress(self, pct: float, msg: str) -> None:
        self.query_one("#progress", ProgressBar).update(total=100, progress=pct)
        self.query_one("#status", Static).update(msg)

    def _show_error(self, error: str) -> None:
        self.query_one("#status", Static).update(f"[bold red]Error: {error}[/bold red]")
        self.query_one("#btn-verify", Button).disabled = False

    def _show_results(self, original: bytes, recovered: bytes, num_pages: int) -> None:
        self.query_one("#progress", ProgressBar).update(total=100, progress=100)
        size_ok = len(original) == len(recovered)
        match_ok = original == recovered
        p = "[green]PASS[/green]"
        f = "[red]FAIL[/red]"
        self.query_one("#status", Static).update(
            f"Pages: {num_pages}\n"
            f"Size:    {p if size_ok else f} ({len(original):,} vs {len(recovered):,} bytes)\n"
            f"Content: {p if match_ok else f}\n"
            f"SHA-256: {p if match_ok else f}\n\n"
            f"{'[bold green]Verification PASSED[/bold green]' if match_ok else '[bold red]Verification FAILED[/bold red]'}"
        )
        self.query_one("#btn-verify", Button).disabled = False
