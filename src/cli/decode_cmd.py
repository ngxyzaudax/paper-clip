from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from cli.display import (
    file_size_display,
    make_page_callback,
    make_page_progress,
    print_error,
    print_success,
)
from common.image_resolver import SUPPORTED_IMAGE_EXTS, is_image_file
from serialization.decode.pipeline import decode

console = Console()


def _describe_source(source: Path) -> tuple[str, int]:
    if source.is_dir():
        image_files: list[Path] = []
        for ext in SUPPORTED_IMAGE_EXTS:
            image_files.extend(source.glob(f"*{ext}"))
        total = sum(f.stat().st_size for f in image_files)
        return f"{len(image_files)} image(s) in {source}", total
    return f"Image: {source.name}", source.stat().st_size


def decode_command(
    input_path: Path = typer.Argument(..., help="Image file or directory of scanned pages"),
    output_file: Path = typer.Option("./decoded_output", help="Output file path"),
    password: str | None = typer.Option(None, help="Decryption password"),
    save_password: str | None = typer.Option(None, help="Save password with this label after success"),
    classifier: str = typer.Option("auto", help="Classifier: auto, ml, or rgb"),
) -> None:
    """Decode paper-clip pages back to the original file.

    Accepts a single image or a directory of scanned images.
    Config is read from page headers automatically.
    """
    if not input_path.exists():
        print_error(f"Not found: {input_path}")
        raise typer.Exit(1)

    if not (is_image_file(input_path) or input_path.is_dir()):
        print_error(f"Unsupported input: {input_path}")
        raise typer.Exit(1)

    description, total_size = _describe_source(input_path)

    table = Table(title="Decoding Plan", show_header=True, header_style="bold cyan")
    table.add_column("Detail", style="bold")
    table.add_column("Value", style="white")
    table.add_row("Source", description)
    table.add_row("Source size", file_size_display(total_size))
    table.add_row("Output file", str(output_file))
    console.print(table)
    console.print()

    progress, task = make_page_progress("Decoding pages")
    with progress:
        result, original_filename = decode(
            input_path, output_file,
            on_page_decoded=make_page_callback(progress, task),
            passphrase=password, classifier=classifier,
        )

    if save_password and password:
        from common.keystore import save_password as store_pw
        store_pw(save_password, password)
        console.print(f"[cyan]Password saved as '{save_password}'[/cyan]")

    final_path = output_file.parent / original_filename if original_filename else output_file
    print_success(f"Decoded {file_size_display(len(result))} to {final_path}")
    if original_filename:
        console.print(f"[cyan]Restored original filename:[/cyan] {original_filename}")
    console.print("[green]SHA-256 integrity check passed[/green]")
