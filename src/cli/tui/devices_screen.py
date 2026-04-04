from textual import work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widget import Widget
from textual.widgets import Button, Checkbox, Select, Static

from common.device_config import (
    get_scanner_settings,
    save_printer_settings,
    save_scanner_settings,
)
from common.types import PrinterInfo, ScannerInfo


class DevicesScreen(Widget):

    def __init__(self) -> None:
        super().__init__()
        self._printers: list[PrinterInfo] = []
        self._scanners: list[ScannerInfo] = []

    def compose(self) -> ComposeResult:
        with VerticalScroll(classes="form-container"):
            yield Static("Hardware Devices", classes="screen-title")
            with Horizontal(classes="form-row"):
                yield Checkbox("Show printers", value=True, id="chk-show-printers")
                yield Checkbox("Show scanners", value=True, id="chk-show-scanners")
            with Horizontal(classes="dual-panel"):
                with Vertical(classes="panel", id="panel-printers"):
                    yield Static("PRINTERS", classes="panel-title")
                    yield Select([], prompt="Discovering...", id="printer-select")
                    yield Static("", id="printer-caps", classes="details-panel")
                with Vertical(classes="panel", id="panel-scanners"):
                    yield Static("SCANNERS", classes="panel-title")
                    yield Select([], prompt="Discovering...", id="scanner-select")
                    yield Static("", id="scanner-caps", classes="details-panel")
            with Horizontal(classes="button-bar"):
                yield Button("Refresh", id="btn-refresh")
                yield Button("Save Defaults", variant="primary", id="btn-save")
            yield Static("", id="status")

    def on_mount(self) -> None:
        self._discover_devices()

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        if event.checkbox.id == "chk-show-printers":
            self.query_one("#panel-printers", Vertical).display = event.value
        elif event.checkbox.id == "chk-show-scanners":
            self.query_one("#panel-scanners", Vertical).display = event.value

    @work(thread=True)
    def _discover_devices(self) -> None:
        self.app.call_from_thread(
            self.query_one("#status", Static).update,
            "[bold]Discovering devices...[/bold]",
        )
        try:
            from cli.tui.devices_worker import discover_printers, discover_scanners
            pr_opts, pr_init = discover_printers(self._printers)
            sc_opts, sc_init = discover_scanners(self._scanners)

            def _update() -> None:
                pr_sel = self.query_one("#printer-select", Select)
                pr_sel.set_options(pr_opts)
                if pr_init != Select.BLANK:
                    pr_sel.value = pr_init
                if not pr_opts:
                    self.query_one("#printer-caps", Static).update("[yellow]No printers found[/yellow]")
                sc_sel = self.query_one("#scanner-select", Select)
                sc_sel.set_options(sc_opts)
                if sc_init != Select.BLANK:
                    sc_sel.value = sc_init
                if not sc_opts:
                    self.query_one("#scanner-caps", Static).update("[yellow]No scanners found[/yellow]")
            self.app.call_from_thread(_update)
            self.app.call_from_thread(self.query_one("#status", Static).update, "")
        except Exception as e:
            self.app.call_from_thread(
                self.query_one("#status", Static).update,
                f"[red]Discovery error: {e}[/red]",
            )

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.value == Select.BLANK:
            return
        if event.select.id == "printer-select":
            self._load_printer_caps(str(event.value))
        elif event.select.id == "scanner-select":
            self._load_scanner_caps(str(event.value))

    @work(thread=True)
    def _load_printer_caps(self, name: str) -> None:
        from cli.tui.devices_worker import format_printer_caps
        text = format_printer_caps(name)
        self.app.call_from_thread(self.query_one("#printer-caps", Static).update, text)

    @work(thread=True)
    def _load_scanner_caps(self, device_id: str) -> None:
        from cli.tui.devices_worker import format_scanner_caps
        text = format_scanner_caps(device_id)
        self.app.call_from_thread(self.query_one("#scanner-caps", Static).update, text)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-refresh":
            self._discover_devices()
        elif event.button.id == "btn-save":
            self._save_defaults()

    def _save_defaults(self) -> None:
        printer_val = self.query_one("#printer-select", Select).value
        scanner_val = self.query_one("#scanner-select", Select).value
        if printer_val != Select.BLANK:
            save_printer_settings(name=str(printer_val))
        if scanner_val != Select.BLANK:
            saved = get_scanner_settings()
            save_scanner_settings(
                device=str(scanner_val),
                dpi=saved.get("dpi", 1200),
                mode=str(saved.get("mode", "Color")),
            )
        self.query_one("#status", Static).update(
            "[bold green]Default devices saved[/bold green]"
        )
