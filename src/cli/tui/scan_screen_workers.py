from pathlib import Path
from typing import Protocol

from textual.app import App

from cli.tui.scan_jobs import ScanJobContext, next_scan_path, start_scan_job, update_scan_job_metadata
from cli.tui.scan_worker import discover_scanners_for_scan, resolve_max_dpi
from common.device_config import get_scanner_settings
from common.scan_capture import capture_page


class ScanPanel(Protocol):
    app: App

    def set_status(self, text: str) -> None: ...

    def apply_discovery(self, options: list[tuple[str, str]], initial: str | None) -> None: ...

    def apply_started(self, job: ScanJobContext, max_dpi: int) -> None: ...

    def apply_scanned(self, path: Path, dpi: int) -> None: ...

    def apply_scan_failed(self, message: str) -> None: ...


def discover_into(panel: ScanPanel) -> None:
    panel.app.call_from_thread(panel.set_status, "[bold]Discovering scanners...[/bold]")
    options, initial = discover_scanners_for_scan()
    panel.app.call_from_thread(panel.apply_discovery, options, initial)


def start_job_into(panel: ScanPanel, device: str) -> None:
    max_dpi = _usable_dpi(device)
    if max_dpi <= 0:
        panel.app.call_from_thread(panel.set_status, "[red]Could not resolve scanner DPI. Check that the scanner is online.[/red]")
        return
    try:
        job = start_scan_job(device, max_dpi)
    except (OSError, ValueError) as exc:
        panel.app.call_from_thread(panel.set_status, f"[red]Could not start the job: {exc}[/red]")
        return
    panel.app.call_from_thread(panel.apply_started, job, max_dpi)


def scan_page_into(panel: ScanPanel, job: ScanJobContext, device: str, max_dpi: int | None) -> None:
    target = next_scan_path(job.job_dir)
    panel.app.call_from_thread(panel.set_status, f"[bold]Scanning {target.stem} at {max_dpi} DPI...[/bold]")
    try:
        result = capture_page(device, target, max_dpi)
    except Exception as exc:
        panel.app.call_from_thread(panel.apply_scan_failed, f"[red]Scan failed: {exc}[/red]")
        return
    update_scan_job_metadata(job.job_dir, result.dpi, result.mode)
    panel.app.call_from_thread(panel.apply_scanned, Path(result.target_path), result.dpi)


def _usable_dpi(device: str) -> int:
    resolved = resolve_max_dpi(device)
    if resolved:
        return resolved
    return int(get_scanner_settings().get("dpi", 0) or 0)
