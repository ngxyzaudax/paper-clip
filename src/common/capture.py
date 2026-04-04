import logging
from collections.abc import Callable
from pathlib import Path

from common.cups_client import print_file
from common.data_store import scans_page_dir, update_job_metadata
from common.scan_session import save_master

logger = logging.getLogger(__name__)

CaptureCallback = Callable[[str], None]
PromptCallback = Callable[[str], bool]


def _do_scan(device: str, dpi: int, mode: str, output_file: Path) -> bool:
    from common.sane_client import scan_page
    image = scan_page(device, dpi, mode)
    if image is None:
        return False
    image.save(str(output_file), format="PNG")
    return True


def run_capture_session(
    job_dir: Path,
    digital_pages: list[Path],
    printer_name: str,
    scanner_device: str,
    scanner_dpi: int,
    scanner_mode: str,
    scans_per_page: int,
    print_resolution: str | None = None,
    on_status: CaptureCallback | None = None,
    on_prompt: PromptCallback | None = None,
) -> list[Path]:
    """Drive a full print+scan capture loop for all pages in a job.

    on_prompt MUST block until the user is ready to proceed.
    If on_prompt is None, an input() fallback is used.
    Returns list of master.png paths, one per page.
    """
    if on_prompt is None:
        on_prompt = _default_prompt

    masters: list[Path] = []

    for page_idx, page_path in enumerate(digital_pages):
        page_num = page_idx + 1
        _notify(on_status, f"Printing page {page_num}/{len(digital_pages)}...")
        job_id = print_file(
            printer_name, page_path,
            title=f"paper-clip page {page_num}",
            resolution=print_resolution,
        )

        if job_id is None:
            _notify(on_status, f"Print failed for page {page_num}, skipping")
            continue

        confirmed = on_prompt(
            f"Page {page_num}/{len(digital_pages)} sent to printer. "
            f"Place printed page on scanner and confirm to start scanning."
        )
        if not confirmed:
            _notify(on_status, f"User cancelled at page {page_num}")
            break

        page_scan_dir = scans_page_dir(job_dir, page_idx)
        scanned: list[Path] = []

        for scan_idx in range(scans_per_page):
            scan_num = scan_idx + 1
            outfile = page_scan_dir / f"scan_{scan_num:03d}.png"
            _notify(on_status, f"Page {page_num}: scanning {scan_num}/{scans_per_page}...")
            if _do_scan(scanner_device, scanner_dpi, scanner_mode, outfile):
                scanned.append(outfile)
                _notify(on_status, f"Page {page_num}: scan {scan_num}/{scans_per_page} saved")
            else:
                _notify(on_status, f"Page {page_num}: scan {scan_num} failed")

        if scanned:
            master = save_master(scanned, page_scan_dir)
            masters.append(master)
            _notify(on_status, f"Page {page_num}: master created from {len(scanned)} scan(s)")
        else:
            _notify(on_status, f"Page {page_num}: no scans succeeded")

    update_job_metadata(job_dir, {"capture_complete": True, "masters": [str(m) for m in masters]})
    return masters


def _default_prompt(msg: str) -> bool:
    input(f"\n{msg}\nPress ENTER when ready...")
    return True


def _notify(cb: CaptureCallback | None, msg: str) -> None:
    logger.info(msg)
    if cb:
        cb(msg)
