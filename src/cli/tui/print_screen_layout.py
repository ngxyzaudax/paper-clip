from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Label, Static

from cli.tui.print_jobs import PrintJob

DUPLEX_OPTIONS: list[tuple[str, str]] = [("Off", "off"), ("On", "on")]


def compose_print_screen() -> ComposeResult:
    with Vertical(classes="encode-screen-layout form-container"):
        with Horizontal(classes="encode-split"):
            with Vertical(classes="encode-form-col"):
                yield Static("Print jobs", classes="encode-panel-title")
                with Vertical(classes="section"):
                    with VerticalScroll(classes="encode-form-scroll"):
                        yield from _picker_row("Printer", "print-printer-pick", "[dim]Discovering…[/dim]", True)
                        yield from _picker_row("Job", "print-job-pick", "[dim]Discovering…[/dim]", True)
                        yield from _picker_row("Duplex", "print-duplex-pick", "Off", False)
            with Vertical(classes="encode-info-col"):
                yield Static("Job details", classes="encode-panel-title")
                with Vertical(classes="section"):
                    with VerticalScroll(classes="encode-info-scroll"):
                        yield Static(
                            "[dim]Loading jobs…[/dim]",
                            id="print-job-details",
                            classes="details-panel",
                        )
        with VerticalScroll(classes="encode-bottom-scroll"):
            with Horizontal(classes="button-bar"):
                yield Button("Refresh", id="btn-print-refresh", compact=True)
                yield Button(
                    "Print Job",
                    id="btn-print-submit",
                    variant="primary",
                    compact=True,
                    disabled=True,
                )
            yield Static("", id="print-status")


def _picker_row(label: str, button_id: str, button_label: str, disabled: bool) -> ComposeResult:
    with Horizontal(classes="form-row"):
        with Vertical(classes="form-col"):
            yield Label(label)
            yield Button(button_label, id=button_id, compact=True, disabled=disabled)


def duplex_label(enabled: bool) -> str:
    return "On" if enabled else "Off"


def format_job_details(job: PrintJob | None, duplex: bool) -> str:
    if job is None:
        return "[dim]Select a job to preview pages[/dim]"
    page_lines = "\n".join(f"  - {page.name}" for page in job.page_paths[:20])
    if len(job.page_paths) > 20:
        page_lines += f"\n  ... ({len(job.page_paths) - 20} more)"
    source = job.source_file if job.source_file else "(unknown source)"
    created = job.created if job.created else "(unknown)"
    paper = job.paper_size if job.paper_size else "(unknown)"
    duplex_text = "on" if duplex else "off"
    return (
        f"[bold]Job[/bold]: {job.job_id}\n"
        f"[bold]Source[/bold]: {source}\n"
        f"[bold]Created[/bold]: {created}\n"
        f"[bold]Paper[/bold]: {paper}\n"
        f"[bold]Duplex[/bold]: {duplex_text}\n"
        f"[bold]Pages[/bold]: {len(job.page_paths)}\n\n"
        f"[bold]Files[/bold]\n{page_lines}"
    )
