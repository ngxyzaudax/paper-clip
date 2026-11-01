import logging
from pathlib import Path
from typing import Protocol

from textual.widgets import Button, ProgressBar, Static

from cli.tui.encode_execution import format_encode_success_message, run_tui_encode_job
from cli.tui.encode_helpers import format_encoding_info_panel, format_encoding_plan
from cli.tui.encoding_form import EncodingFormPicks
from common.config import PaperClipConfig
from common.paper_sizes import config_with_page_dimensions
from common.perf import log_phase


class _EncodeHost(Protocol):
    _config: PaperClipConfig | None
    _picks: EncodingFormPicks
    _input_path: Path | None
    _passphrase: str | None
    last_job_id: str | None
    app: object

    def query_one(self, selector: str, expect_type: type | None = None): ...


def rebuild_encode_screen(screen: _EncodeHost) -> None:
    logger = logging.getLogger(__name__)
    info = screen.query_one("#encode-info-display", Static)
    try:
        with log_phase(logger, "tui.EncodeScreen.resolve_form"):
            base = resolve_encoding_form_of(screen)
            screen._config = config_with_page_dimensions(base, screen._picks.paper_size)
        with log_phase(logger, "tui.EncodeScreen.update_info_display"):
            info.update(format_encoding_info_panel(screen._config, screen._picks.paper_size))
    except Exception as exc:
        screen._config = None
        info.update(f"[red]{exc}[/red]")
    with log_phase(logger, "tui.EncodeScreen.update_encoding_plan"):
        update_encode_plan(screen)


def resolve_encoding_form_of(screen: _EncodeHost):
    from cli.tui.encoding_form import resolve_encoding_form
    return resolve_encoding_form(screen._picks)


def update_encode_plan(screen: _EncodeHost) -> None:
    plan = screen.query_one("#encoding-plan", Static)
    button = screen.query_one("#btn-encode", Button)
    if not screen._config or not screen._input_path:
        plan.update("[dim]Set encoding parameters and select an input file[/dim]")
        button.disabled = True
        return
    plan.update(format_encoding_plan(screen._config, screen._input_path, screen._passphrase))
    button.disabled = False


def run_encode_job(screen: _EncodeHost) -> None:
    job_id: str | None = None
    try:
        message, job_id = _encoded_message(screen)
    except Exception as exc:
        message = f"[bold red]Error: {exc}[/bold red]"
    screen.app.call_from_thread(_finish_encode, screen, message, job_id)


def _finish_encode(screen: _EncodeHost, message: str, job_id: str | None) -> None:
    screen.last_job_id = job_id
    screen.query_one("#btn-encode-print", Button).disabled = job_id is None
    set_encode_progress(screen, 100, message, True)


def set_encode_progress(screen: _EncodeHost, pct: float, message: str, done: bool = False) -> None:
    screen.query_one("#progress", ProgressBar).update(total=100, progress=100 if done else pct)
    screen.query_one("#status", Static).update(message)
    if done:
        screen.query_one("#btn-encode", Button).disabled = False


def _encoded_message(screen: _EncodeHost) -> tuple[str, str]:
    config, input_path, passphrase = screen._config, screen._input_path, screen._passphrase
    if config is None or input_path is None:
        raise ValueError("Invalid configuration")

    def on_page(idx: int, total: int, path: Path | None) -> None:
        del path
        screen.app.call_from_thread(
            set_encode_progress, screen, ((idx + 1) / total) * 100, f"Page {idx + 1}/{total}",
        )

    job_dir, png_paths = run_tui_encode_job(
        config=config, input_path=input_path, passphrase=passphrase, on_page_complete=on_page,
    )
    return format_encode_success_message(job_dir, png_paths), Path(job_dir).name
