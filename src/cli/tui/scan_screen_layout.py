from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Label, Static


def compose_scan_screen() -> ComposeResult:
    with Vertical(classes="encode-screen-layout form-container"):
        with Horizontal(classes="encode-split"):
            with Vertical(classes="encode-form-col"):
                yield Static("Scan job", classes="encode-panel-title")
                with Vertical(classes="section"):
                    with VerticalScroll(classes="encode-form-scroll"):
                        with Horizontal(classes="form-row"):
                            with Vertical(classes="form-col"):
                                yield Label("Scanner")
                                yield Button(
                                    "[dim]Discovering…[/dim]",
                                    id="scan-scanner-pick",
                                    compact=True,
                                    disabled=True,
                                )
            with Vertical(classes="encode-info-col"):
                yield Static("Job details", classes="encode-panel-title")
                with Vertical(classes="section"):
                    with VerticalScroll(classes="encode-info-scroll"):
                        yield Static(
                            "[dim]Discovering scanner…[/dim]",
                            id="scan-job-details",
                            classes="details-panel",
                        )
        with VerticalScroll(classes="encode-bottom-scroll"):
            with Horizontal(classes="button-bar"):
                yield Button("Refresh", id="btn-scan-refresh", compact=True)
                yield Button(
                    "Start Scan Job",
                    id="btn-scan-start",
                    variant="primary",
                    compact=True,
                    disabled=True,
                )
                yield Button(
                    "Scan Next Page",
                    id="btn-scan-next",
                    variant="success",
                    compact=True,
                    disabled=True,
                )
                yield Button(
                    "Finish",
                    id="btn-scan-finish",
                    compact=True,
                    disabled=True,
                )
            yield Static("", id="scan-status")


def format_scanner_state(
    scanner_label: str,
    max_dpi: int | None,
    job_id: str | None,
    page_count: int,
    last_path: str,
) -> str:
    if not scanner_label:
        return "[dim]No scanner available. Configure one under Hardware > Devices.[/dim]"
    dpi_line = f"{max_dpi} DPI" if max_dpi else "DPI unknown"
    if job_id is None:
        return (
            f"[bold]Scanner[/bold]: {scanner_label}\n"
            f"[bold]Max DPI[/bold]: {dpi_line}\n\n"
            "[dim]No active job. Press 'Start Scan Job' to begin.[/dim]"
        )
    last_line = last_path if last_path else "(none yet)"
    return (
        f"[bold]Scanner[/bold]: {scanner_label}\n"
        f"[bold]Max DPI[/bold]: {dpi_line}\n"
        f"[bold]Active job[/bold]: {job_id}\n"
        f"[bold]Pages captured[/bold]: {page_count}\n"
        f"[bold]Last saved[/bold]: {last_line}"
    )
