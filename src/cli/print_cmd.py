from pathlib import Path

import typer

from cli.display import print_error, print_success
from common.device_discover import list_ipp_printers
from common.device_error import DeviceError
from common.device_config import get_printer_settings
from common.ipp_media import MEDIA_SIZES
from common.ipp_print import print_pages


def print_command(
    page: Path = typer.Argument(..., help="PNG page to print"),
    printer_uri: str | None = typer.Option(None, "--uri", help="IPP or IPPS printer URI"),
    paper: str | None = typer.Option(None, "--paper", help="Paper size, default A4"),
) -> None:
    """Print a page over IPP Everywhere. Borderless and fit-to-page are refused."""
    if not page.exists():
        print_error(f"Page not found: {page}")
        raise typer.Exit(1)
    try:
        uri = printer_uri or _saved_or_only_printer()
        chosen = paper or str(get_printer_settings().get("paper_size") or "A4")
        if chosen not in MEDIA_SIZES:
            raise DeviceError(f"unsupported paper size: {chosen}")
        job_ids = print_pages(uri, [page], f"paper-clip {page.name}", chosen)
    except DeviceError as exc:
        print_error(str(exc))
        raise typer.Exit(1) from exc
    print_success(f"Printed {page.name} as IPP job {job_ids[0]} on {uri}")


def _saved_or_only_printer() -> str:
    saved = str(get_printer_settings().get("uri", ""))
    if saved:
        return saved
    found = list_ipp_printers()
    if len(found) == 1:
        return found[0].uri
    if not found:
        raise DeviceError("no IPP printer found; pass --uri or set printer.uri")
    listed = ", ".join(item.uri for item in found)
    raise DeviceError(f"multiple IPP printers; pass --uri ({listed})")
