from pathlib import Path

import typer

from cli.display import print_error, print_success
from serialization.decode.errors import DecodeError
from serialization.decode.pipeline import decode


def decode_command(
    source: Path = typer.Argument(..., help="Scan image, directory, or scan job directory"),
    output: Path | None = typer.Option(None, "--output", "-o", help="Output file or directory"),
    password: str | None = typer.Option(None, help="User passphrase, when the page was encrypted with one"),
    model: Path | None = typer.Option(None, "--model", help="Saved Keras cell decoder"),
    no_model: bool = typer.Option(False, "--no-model", help="Classify cells by calibrated nearest colour only"),
) -> None:
    """Read scanned pages back into the original file."""
    if not source.exists():
        print_error(f"Scan source not found: {source}")
        raise typer.Exit(1)
    try:
        raw, filename = decode(
            source,
            passphrase=password,
            model_path=model,
            use_model=False if no_model else None,
        )
    except DecodeError as exc:
        print_error(str(exc))
        raise typer.Exit(1) from exc
    destination = _destination(output, source, filename)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(raw)
    print_success(f"Recovered {filename} ({len(raw)} bytes) -> {destination}")


def _destination(output: Path | None, source: Path, filename: str) -> Path:
    if output is None:
        return Path.cwd() / filename
    if output.is_dir():
        return output / filename
    return output
