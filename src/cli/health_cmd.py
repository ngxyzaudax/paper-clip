from pathlib import Path

import typer

from cli.display import console, print_error, print_success
from cli.health_print import print_check, print_health, print_history, print_tracked
from cli.open_file import open_with_system
from health.check import HealthCheck, run_check
from health.reading import Tracked, latest
from health.store import all_tracked, find_tracked, forget_tracked
from serialization.decode.errors import DecodeError

health_app = typer.Typer(
    help="Track how well printed pages hold up. Every decode adds a reading; 0% means the data is lost.",
    invoke_without_command=True,
)


@health_app.callback()
def health_callback(ctx: typer.Context) -> None:
    """List tracked files when no subcommand is given."""
    if ctx.invoked_subcommand is None:
        print_tracked(all_tracked())


@health_app.command("list")
def list_command() -> None:
    """Every tracked file with its latest health, newest check first."""
    print_tracked(all_tracked())


@health_app.command("show")
def show_command(
    file: str = typer.Argument(..., help="File name or the first characters of its ID"),
    open_image: bool = typer.Option(False, "--open", help="Open the latest damage image"),
) -> None:
    """Latest health, trend, advice, damage map, and every past check of one file."""
    history = _tracked_or_exit(file)
    print_health(history, f"[dim]{len(history.readings)} check(s)[/]")
    print_history(history)
    if open_image:
        _open_image(history)


@health_app.command("check")
def check_command(
    source: Path = typer.Argument(..., help="Scan image, directory, or scan job directory"),
    password: str | None = typer.Option(None, help="User passphrase, when the page was encrypted with one"),
    model: Path | None = typer.Option(None, "--model", help="Saved Keras cell decoder"),
    no_model: bool = typer.Option(False, "--no-model", help="Classify cells by calibrated nearest colour only"),
    no_track: bool = typer.Option(False, "--no-track", help="Show the result without saving it to the history"),
    open_image: bool = typer.Option(False, "--open", help="Open the damage image when done"),
) -> None:
    """Rate scanned pages without writing the recovered file."""
    check = checked_or_exit(source, password, model, no_model, not no_track)
    print_check(check)
    if open_image:
        _open_image(check.history)
    if check.decoded is None:
        raise typer.Exit(1)


@health_app.command("forget")
def forget_command(
    file: str = typer.Argument(..., help="File name or the first characters of its ID"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Do not ask for confirmation"),
) -> None:
    """Delete a file's health history. Damage images stay on disk."""
    history = _tracked_or_exit(file)
    label = history.filename or history.sha256[:12]
    if not yes and not typer.confirm(f"Forget {len(history.readings)} check(s) of {label}?"):
        raise typer.Exit(0)
    forget_tracked(history.sha256)
    print_success(f"Forgot the health history of {label}")


def checked_or_exit(
    source: Path, password: str | None, model: Path | None, no_model: bool, track: bool,
) -> HealthCheck:
    if not source.exists():
        print_error(f"Scan source not found: {source}")
        raise typer.Exit(1)
    try:
        with console.status("Reading scans and measuring paper health..."):
            return run_check(source, password, model, False if no_model else None, track)
    except DecodeError as exc:
        print_error(str(exc))
        raise typer.Exit(1) from exc


def _tracked_or_exit(file: str) -> Tracked:
    history = find_tracked(file)
    if history is None:
        print_error(f"No tracked file matches {file!r}. Run paper-clip health to list them.")
        raise typer.Exit(1)
    return history


def _open_image(history: Tracked) -> None:
    image = latest(history).damage_image
    if not image or not Path(image).is_file():
        print_error("This check has no damage image.")
    elif not open_with_system(Path(image)):
        print_error(f"Could not open {image}")
