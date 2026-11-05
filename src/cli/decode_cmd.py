from pathlib import Path

import typer

from cli.display import print_error, print_success
from cli.health_cmd import checked_or_exit
from cli.health_print import print_check
from common.decode_output import decode_destination, write_recovered


def decode_command(
    source: Path = typer.Argument(..., help="Scan image, directory, or scan job directory"),
    output: Path | None = typer.Option(None, "--output", "-o", help="Output file or directory"),
    password: str | None = typer.Option(None, help="User passphrase, when the page was encrypted with one"),
    model: Path | None = typer.Option(None, "--model", help="Saved Keras cell decoder"),
    no_model: bool = typer.Option(False, "--no-model", help="Classify cells by calibrated nearest colour only"),
    force: bool = typer.Option(False, "--force", help="Overwrite the output file when it already exists"),
    no_track: bool = typer.Option(False, "--no-track", help="Do not add this reading to the paper health history"),
) -> None:
    """Read scanned pages back into the original file and rate the paper's health. Existing files are kept unless --force."""
    check = checked_or_exit(source, password, model, no_model, not no_track)
    print_check(check)
    if check.decoded is None:
        print_error("The file could not be recovered from these scans. Try a cleaner rescan or another copy.")
        raise typer.Exit(1)
    decoded = check.decoded
    destination = write_recovered(decode_destination(output, decoded.filename, force), decoded.raw)
    print_success(f"Recovered {decoded.filename} ({len(decoded.raw):,} bytes) -> {destination}")
