from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Input, Label, LoadingIndicator, Static


def compose_decode_screen() -> ComposeResult:
    with Vertical(classes="encode-screen-layout form-container"):
        with Horizontal(classes="encode-split"):
            with Vertical(classes="encode-form-col"):
                yield Static("Decode scans", classes="encode-panel-title")
                with Vertical(classes="section"):
                    with VerticalScroll(classes="encode-form-scroll"):
                        with Horizontal(classes="form-row"):
                            with Vertical(classes="form-col"):
                                yield Label("Scan job")
                                yield Button("[dim]Loading...[/dim]", id="dec-job-pick", compact=True, disabled=True)
                        with Horizontal(classes="form-row"):
                            with Vertical(classes="form-col"):
                                yield Label("Or a folder of scans")
                                yield Button("Browse...", id="dec-browse", compact=True)
                        with Vertical(classes="encode-password-block"):
                            yield Label("Password")
                            yield Input(
                                placeholder="only if the file was encoded with one",
                                password=True,
                                id="dec-password",
                                compact=True,
                            )
            with Vertical(classes="encode-info-col"):
                yield Static("Details", classes="encode-panel-title")
                with Vertical(classes="section"):
                    with VerticalScroll(classes="encode-info-scroll"):
                        yield Static("[dim]Pick a scan job.[/dim]", id="dec-details", classes="details-panel")
        with VerticalScroll(classes="encode-bottom-scroll"):
            with Horizontal(classes="button-bar"):
                yield Button("Refresh", id="dec-refresh", compact=True)
                yield Button("Decode", id="dec-run", variant="primary", compact=True, disabled=True)
            with Horizontal(id="dec-status-row"):
                yield LoadingIndicator(id="dec-busy")
                yield Static("", id="dec-status")


DECODE_CSS = """
DecodeScreen {
    width: 100%;
    height: 100%;
}
DecodeScreen #dec-status-row {
    height: auto;
}
DecodeScreen #dec-busy {
    width: 4;
    height: 1;
    display: none;
}
DecodeScreen #dec-busy.busy {
    display: block;
}
DecodeScreen #dec-status {
    width: 1fr;
    height: auto;
}
"""
