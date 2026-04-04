from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widget import Widget
from textual.widgets import Button, Input, Label, Static

from cli.config_cmd import format_config_description, format_profiles_listing
from common.config import default_config, load_config, save_config


class ConfigScreen(Widget):

    def compose(self) -> ComposeResult:
        with VerticalScroll(classes="form-container"):
            yield Static("Configuration", classes="screen-title")
            with Vertical(classes="section"):
                yield Static("Profiles", classes="section-title")
                yield Static("", id="profiles-list", classes="details-panel")
                yield Button("Refresh profile list", id="btn-profiles-refresh")
            with Vertical(classes="section"):
                yield Static("Inspect TOML", classes="section-title")
                with Horizontal(classes="picker-row"):
                    yield Static("[dim]No file selected[/dim]", id="toml-label")
                    yield Button("Browse...", id="toml-browse")
                yield Static("", id="toml-inspect", classes="details-panel")
            with Vertical(classes="section"):
                yield Static("Export default template", classes="section-title")
                yield Label("Output file path")
                yield Input(value="./paper_clip_default.toml", id="export-path")
                yield Button("Write default config", id="btn-export", variant="primary")
            yield Static("", id="status")

    def on_mount(self) -> None:
        self._refresh_profiles()

    def _refresh_profiles(self) -> None:
        self.query_one("#profiles-list", Static).update(format_profiles_listing())

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-profiles-refresh":
            self._refresh_profiles()
        elif event.button.id == "toml-browse":
            from cli.tui.file_picker import FilePickerScreen
            self.app.push_screen(
                FilePickerScreen(mode="file", title="Select config TOML"),
                callback=self._on_toml_picked,
            )
        elif event.button.id == "btn-export":
            self._export_default()

    def _on_toml_picked(self, result: Path | None) -> None:
        if result is None:
            return
        self.query_one("#toml-label", Static).update(str(result))
        if not result.exists():
            self.query_one("#toml-inspect", Static).update("[red]File not found[/red]")
            return
        try:
            cfg = load_config(result)
            self.query_one("#toml-inspect", Static).update(format_config_description(cfg))
        except Exception as e:
            self.query_one("#toml-inspect", Static).update(f"[red]{e}[/red]")

    def _export_default(self) -> None:
        out = Path(self.query_one("#export-path", Input).value).expanduser()
        try:
            cfg = default_config()
            save_config(cfg, out)
            self.query_one("#status", Static).update(
                f"[bold green]Saved default configuration to {out}[/bold green]\n"
                f"{format_config_description(cfg)}",
            )
        except Exception as e:
            self.query_one("#status", Static).update(f"[red]{e}[/red]")
