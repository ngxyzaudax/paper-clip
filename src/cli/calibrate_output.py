from pathlib import Path

import typer

from calibration.sheet_io import calibration_dir, sheet_ready
from calibration.sheet_limits import axis_limits, choose_profile
from calibration.sheet_report import format_limits
from calibration.sheet_score import PatchRead
from cli.display import print_error


def show_limits(reads: tuple[PatchRead, ...]) -> None:
    if not reads:
        print_error("No calibration patches were read. Scan the sheet with `paper-clip calibrate scan`.")
        raise typer.Exit(1)
    typer.echo(format_limits(axis_limits(reads), choose_profile(reads)))


def require_clean(reads: tuple[PatchRead, ...]) -> None:
    bad = [read.name for read in reads if not _clean(read)]
    if bad:
        print_error(f"Digital check failed: {', '.join(bad[:6])}")
        raise typer.Exit(1)


def require_sheet() -> Path:
    if not sheet_ready():
        print_error("The sheet is missing or out of date. Run `paper-clip calibrate sheet` first.")
        raise typer.Exit(1)
    return calibration_dir()


def confirm_or_exit(yes: bool, question: str) -> None:
    if not yes and not typer.confirm(question):
        typer.echo("Cancelled. Nothing was changed.")
        raise typer.Exit(0)


def _clean(read: PatchRead) -> bool:
    if read.kind == "qr":
        return read.decoded
    return read.accuracy >= 0.99 and not read.slipped and read.tags_found >= read.tags_expected
