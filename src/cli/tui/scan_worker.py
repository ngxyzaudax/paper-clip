from pathlib import Path

from common.device_config import get_scanner_settings, save_scanner_settings
from common.sane_client import list_scanners, scan_page
from common.scan_session import save_master, session_dir
from common.types import ScannerInfo
from textual.widgets import Select


def discover_scanners() -> tuple[list[tuple[str, str]], "str | type", str]:
    scanners = list_scanners()
    saved = get_scanner_settings()
    options = [
        (f"{s.vendor} {s.model}" if s.vendor else s.device_id, s.device_id)
        for s in scanners
    ]
    saved_device = saved.get("device", "")
    initial = saved_device if any(s.device_id == saved_device for s in scanners) else Select.BLANK
    saved_dpi = str(saved.get("dpi", 1200))
    return options, initial, saved_dpi


def load_dpi_options(device_id: str, saved_dpi: str) -> tuple[list[tuple[str, str]], "str | type"]:
    from common.sane_client import get_scanner_capabilities
    caps = get_scanner_capabilities(device_id)
    if caps and caps.resolutions:
        options = [(f"{r} DPI", str(r)) for r in caps.resolutions]
    else:
        options = [(f"{d} DPI", str(d)) for d in [300, 600, 1200]]
    initial = saved_dpi if any(v == saved_dpi for _, v in options) else Select.BLANK
    return options, initial


def run_scan_session(
    device: str,
    dpi: int,
    count: int,
    base_dir: Path,
    on_progress: "callable | None" = None,
) -> tuple[str, list[Path]]:
    save_scanner_settings(device=device, dpi=dpi)
    run_dir = session_dir(base_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    scanned: list[Path] = []
    for i in range(count):
        if on_progress:
            on_progress(i, count)
        outfile = run_dir / f"scan_{i + 1:03d}.png"
        image = scan_page(device, dpi)
        if image is not None:
            image.save(str(outfile), format="PNG")
            scanned.append(outfile)

    if scanned:
        master = save_master(scanned, run_dir)
        msg = (
            f"[bold green]{len(scanned)}/{count} scans saved[/bold green]\n"
            f"Session: {run_dir}\nMaster: {master.name}"
        )
    else:
        msg = "[bold red]All scans failed[/bold red]"

    return msg, scanned
