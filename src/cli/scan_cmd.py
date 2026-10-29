from pathlib import Path

import typer

from cli.display import print_error, print_success
from common.device_config import get_scanner_settings
from common.device_discover import list_escl_scanners, saved_scanner_uri
from common.device_error import DeviceError
from common.scan_capture import capture_page


def scan_command(
    output: Path = typer.Argument(..., help="Where to write the scan"),
    scanner_uri: str | None = typer.Option(None, "--uri", help="eSCL scanner base URI"),
    dpi: int | None = typer.Option(None, "--dpi", help="Scan resolution; default 1200, or 100 for a preview"),
) -> None:
    """Scan one page over eSCL. Falls back to SANE only when the device id is not an HTTP URI."""
    chosen = dpi if dpi is not None else int(get_scanner_settings().get("dpi", 1200) or 1200)
    try:
        uri = scanner_uri or _saved_or_only_scanner()
        result = capture_page(uri, output, chosen)
    except DeviceError as exc:
        print_error(str(exc))
        raise typer.Exit(1) from exc
    print_success(f"Saved {result.target_path} at {result.dpi} dpi ({result.mode}, {result.source})")


def _saved_or_only_scanner() -> str:
    saved = saved_scanner_uri()
    if saved:
        return saved
    found = list_escl_scanners()
    if len(found) == 1:
        return found[0].device_id
    if not found:
        raise DeviceError("no eSCL scanner found; pass --uri or set scanner.uri")
    listed = ", ".join(item.device_id for item in found)
    raise DeviceError(f"multiple eSCL scanners; pass --uri ({listed})")
