from __future__ import annotations

from functools import partial
from typing import Literal

from textual import work
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Button, Static

from cli.tui.devices_screen_layout import compose_devices_screen
from cli.tui.devices_worker import (
    discover_printers,
    discover_scanners,
    format_printer_caps,
    format_scanner_caps,
    pick_button_label,
    printer_section_placeholder,
    scanner_section_placeholder,
)
from cli.tui.option_picker_screen import OptionPickerScreen
from common.device_config import get_scanner_settings, save_printer_settings, save_scanner_settings
from common.types import PrinterInfo, ScannerInfo


class DevicesScreen(Widget):

    def __init__(self) -> None:
        super().__init__()
        self._printers: list[PrinterInfo] = []
        self._scanners: list[ScannerInfo] = []
        self._printer_options: list[tuple[str, str]] = []
        self._scanner_options: list[tuple[str, str]] = []
        self._printer_name: str | None = None
        self._scanner_device: str | None = None

    def compose(self) -> ComposeResult:
        yield from compose_devices_screen()

    def on_mount(self) -> None:
        self._discover_devices()

    def _refresh_pick_labels(self) -> None:
        pr_btn = self.query_one("#printer-pick", Button)
        sc_btn = self.query_one("#scanner-pick", Button)
        pr_btn.label = pick_button_label(
            self._printer_options,
            self._printer_name,
            absent_message="[dim]No printers found[/dim]",
        )
        sc_btn.label = pick_button_label(
            self._scanner_options,
            self._scanner_device,
            absent_message="[dim]No scanners found[/dim]",
        )
        pr_btn.disabled = not self._printer_options
        sc_btn.disabled = not self._scanner_options

    def _sync_capability_section(self, which: Literal["printer", "scanner"]) -> None:
        if which == "printer":
            opts, sel = self._printer_options, self._printer_name
            ph = printer_section_placeholder(opts, sel)
            wid = "#printer-caps"
        else:
            opts, sel = self._scanner_options, self._scanner_device
            ph = scanner_section_placeholder(opts, sel)
            wid = "#scanner-caps"
        if ph is not None:
            self.query_one(wid, Static).update(ph)
        else:
            self._load_caps(which, sel or "")

    @work(thread=True)
    def _discover_devices(self) -> None:
        self.app.call_from_thread(
            self.query_one("#status", Static).update,
            "[bold]Discovering devices...[/bold]",
        )
        try:
            pr_opts, pr_init = discover_printers(self._printers)
            sc_opts, sc_init = discover_scanners(self._scanners)

            def _update() -> None:
                self._printer_options = pr_opts
                self._scanner_options = sc_opts
                self._printer_name = pr_init
                self._scanner_device = sc_init
                self._refresh_pick_labels()
                self._sync_capability_section("printer")
                self._sync_capability_section("scanner")

            self.app.call_from_thread(_update)
            self.app.call_from_thread(self.query_one("#status", Static).update, "")
        except Exception as e:
            self.app.call_from_thread(
                self.query_one("#status", Static).update,
                f"[red]Discovery error: {e}[/red]",
            )

    def _open_device_picker(self, which: Literal["printer", "scanner"]) -> None:
        opts = self._printer_options if which == "printer" else self._scanner_options
        title = "Printer" if which == "printer" else "Scanner"
        if not opts:
            return
        self.app.push_screen(
            OptionPickerScreen(title, opts),
            partial(self._on_device_picked, which),
        )

    def _on_device_picked(self, which: Literal["printer", "scanner"], result: object | None) -> None:
        if result is None:
            return
        s = str(result)
        if which == "printer":
            self._printer_name = s
        else:
            self._scanner_device = s
        self._refresh_pick_labels()
        self._sync_capability_section(which)

    @work(thread=True)
    def _load_caps(self, which: Literal["printer", "scanner"], key: str) -> None:
        text = format_printer_caps(key) if which == "printer" else format_scanner_caps(key)
        wid = "#printer-caps" if which == "printer" else "#scanner-caps"
        self.app.call_from_thread(self.query_one(wid, Static).update, text)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "btn-refresh":
            self._discover_devices()
        elif bid == "btn-save":
            self._save_defaults()
        elif bid == "printer-pick":
            self._open_device_picker("printer")
        elif bid == "scanner-pick":
            self._open_device_picker("scanner")

    def _save_defaults(self) -> None:
        printer = next((item for item in self._printers if item.uri == self._printer_name), None)
        if printer is not None:
            save_printer_settings(name=printer.name, uri=printer.uri)
        if self._scanner_device:
            saved = get_scanner_settings()
            save_scanner_settings(
                device=self._scanner_device,
                uri=self._scanner_device if self._scanner_device.startswith(("http://", "https://")) else "",
                dpi=int(saved.get("dpi", 1200) or 1200),
                mode=str(saved.get("mode", "Color")),
            )
        self.query_one("#status", Static).update("[bold green]Default devices saved[/bold green]")
