from pathlib import Path
from typing import NamedTuple

from common.decode_output import job_destination, write_recovered
from serialization.decode.errors import DecodeError
from serialization.decode.pipeline import decode


class DecodeResult(NamedTuple):
    filename: str
    size: int
    path: Path


def decode_source(source: Path, label: str, passphrase: str | None) -> DecodeResult:
    """Decode a scan job or folder and save the file under data/decoded/<label>/ without overwriting."""
    raw, filename = decode(source, passphrase=passphrase)
    target = write_recovered(job_destination(label, filename), raw)
    return DecodeResult(filename, len(raw), target)


def decode_result_text(result: DecodeResult) -> str:
    return (
        f"[bold green]Recovered {result.filename}[/bold green]\n"
        f"[bold]Size[/bold]: {result.size:,} bytes\n"
        f"[bold]Saved to[/bold]: {result.path}"
    )


def decode_error_text(exc: Exception) -> str:
    if isinstance(exc, DecodeError):
        return f"[red]Could not decode: {exc}[/red]\n[dim]Check that every page was scanned and the password is right.[/dim]"
    if isinstance(exc, FileNotFoundError):
        return f"[red]Scan source not found: {exc.filename}[/red]"
    return f"[red]Decode failed: {exc}[/red]"
