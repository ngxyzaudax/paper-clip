from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Label, Static


def compose_devices_screen() -> ComposeResult:
    with Vertical(classes="encode-screen-layout form-container"):
        with Horizontal(classes="encode-split"):
            with Vertical(classes="encode-form-col"):
                yield Static("Hardware devices", classes="encode-panel-title")
                with Vertical(classes="section"):
                    with VerticalScroll(classes="encode-form-scroll"):
                        with Horizontal(classes="form-row"):
                            with Vertical(classes="form-col"):
                                yield Label("Printer")
                                yield Button(
                                    "[dim]Discovering…[/dim]",
                                    id="printer-pick",
                                    compact=True,
                                    disabled=True,
                                )
                            with Vertical(classes="form-col"):
                                yield Label("Scanner")
                                yield Button(
                                    "[dim]Discovering…[/dim]",
                                    id="scanner-pick",
                                    compact=True,
                                    disabled=True,
                                )
            with Vertical(classes="encode-info-col"):
                yield Static("Capabilities", classes="encode-panel-title")
                with Vertical(classes="section"):
                    with VerticalScroll(classes="encode-info-scroll"):
                        with Vertical(classes="device-detail-block"):
                            yield Static("Printer", classes="section-title")
                            yield Static(
                                "[dim]Discovering hardware…[/dim]",
                                id="printer-caps",
                                classes="details-panel",
                            )
                        with Vertical(classes="device-detail-block device-detail-block-spaced"):
                            yield Static("Scanner", classes="section-title")
                            yield Static(
                                "[dim]Discovering hardware…[/dim]",
                                id="scanner-caps",
                                classes="details-panel",
                            )
        with VerticalScroll(classes="encode-bottom-scroll"):
            with Horizontal(classes="button-bar"):
                yield Button("Refresh", id="btn-refresh", compact=True)
                yield Button(
                    "Save Defaults",
                    variant="primary",
                    id="btn-save",
                    compact=True,
                )
            yield Static("", id="status")
