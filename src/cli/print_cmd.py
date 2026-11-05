from pathlib import Path

import typer

from cli.display import print_error, print_success
from common.device_config import get_printer_settings
from common.device_discover import list_ipp_printers
from common.device_error import DeviceError
from common.ipp_media import MEDIA_SIZES
from common.ipp_print import print_pages
from common.types import PrinterInfo
from workflows.device_pick import choose_printer


def print_command(
    pages: list[Path] = typer.Argument(..., help="PNG pages in print order"),
    printer_uri: str | None = typer.Option(None, "--uri", help="IPP or IPPS printer URI"),
    paper: str | None = typer.Option(None, "--paper", help="Paper size, default A4"),
    duplex: bool = typer.Option(
        False,
        "--duplex",
        help="Print both sides of each sheet. Off by default. Fails if the printer cannot duplex a PWG document.",
    ),
) -> None:
    """Print pages over IPP Everywhere. Borderless and fit-to-page are refused."""
    if not pages:
        print_error("no pages to print")
        raise typer.Exit(1)
    missing = _first_missing(pages)
    if missing is not None:
        print_error(f"Page not found: {missing}")
        raise typer.Exit(1)
    try:
        uri = printer_uri or _saved_or_only_printer()
        chosen = paper or str(get_printer_settings().get("paper_size") or "A4")
        if chosen not in MEDIA_SIZES:
            raise DeviceError(f"unsupported paper size: {chosen}")
        job_ids = print_pages(uri, pages, _job_title(pages), chosen, duplex=duplex)
    except DeviceError as exc:
        print_error(str(exc))
        raise typer.Exit(1) from exc
    print_success(_success(pages, job_ids, uri, duplex))


def _first_missing(pages: list[Path]) -> Path | None:
    return next((page for page in pages if not page.exists()), None)


def _job_title(pages: list[Path]) -> str:
    if len(pages) == 1:
        return f"paper-clip {pages[0].name}"
    return f"paper-clip {len(pages)} pages"


def _success(pages: list[Path], job_ids: list[int], uri: str, duplex: bool) -> str:
    if len(pages) == 1 and not duplex:
        return f"Printed {pages[0].name} as IPP job {job_ids[0]} on {uri}"
    ids = ", ".join(str(job_id) for job_id in job_ids)
    sides = " on both sides" if duplex else ""
    if len(pages) == 1:
        return f"Printed {pages[0].name}{sides} as IPP job {ids} on {uri}"
    return f"Printed {len(pages)} pages{sides} as IPP job {ids} on {uri}"


def _saved_or_only_printer() -> str:
    return choose_printer(get_printer_settings(), _listed_printers)


def _listed_printers() -> list[PrinterInfo]:
    return list_ipp_printers()
