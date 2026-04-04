import tempfile
from pathlib import Path

import numpy as np
import typer
from rich.console import Console
from rich.table import Table

from cli.display import (
    make_page_callback,
    make_page_progress,
    print_error,
    print_success,
)
from common.config import PaperClipConfig, resolve_config
from common.config_store import load_profile
from serialization.decode.pipeline import decode
from serialization.encode.pipeline import render_pages

console = Console()


def _status_badge(ok: bool) -> str:
    return "[bold green]PASS[/bold green]" if ok else "[bold red]FAIL[/bold red]"


def _pil_images_to_bgr(images: list) -> list[np.ndarray]:
    return [np.array(img.convert("RGB"))[:, :, ::-1] for img in images]


def _execute_verification(input_path: Path, config: PaperClipConfig) -> None:
    original = input_path.read_bytes()

    enc_progress, enc_task = make_page_progress("Rendering")
    with enc_progress:
        pil_images = render_pages(
            input_path, config,
            on_page_complete=make_page_callback(enc_progress, enc_task),
        )
    console.print(f"  [dim]Rendered {len(pil_images)} page(s)[/dim]")

    bgr_images = _pil_images_to_bgr(pil_images)

    with tempfile.TemporaryDirectory() as tmpdir:
        dec_progress, dec_task = make_page_progress("Decoding", total=len(bgr_images))
        with dec_progress:
            recovered, _ = decode(
                bgr_images, Path(tmpdir) / "decoded",
                on_page_decoded=make_page_callback(dec_progress, dec_task),
            )

    size_match = len(original) == len(recovered)
    content_match = original == recovered

    table = Table(title="Verification Results", show_header=True, header_style="bold cyan")
    table.add_column("Check", style="bold")
    table.add_column("Result")
    table.add_column("Detail", style="dim")
    table.add_row("Size match", _status_badge(size_match), f"{len(original):,} vs {len(recovered):,} bytes")
    table.add_row("Content match", _status_badge(content_match), "byte-for-byte comparison")
    table.add_row("SHA-256 verified", _status_badge(content_match), "cryptographic integrity")
    console.print(table)

    if content_match:
        print_success("Roundtrip verification PASSED")
    else:
        print_error("Roundtrip verification FAILED")
        raise typer.Exit(1)


def verify_command(
    input_file: Path = typer.Argument(..., help="File to roundtrip test"),
    profile: str | None = typer.Option(None, help="Config profile name from configs/"),
    config_file: Path | None = typer.Option(None, help="Config TOML file"),
    num_colors: int | None = typer.Option(None, help="Override num_colors"),
    cell_size_px: int | None = typer.Option(None, help="Override cell_size_px"),
    paper_size: str | None = typer.Option(None, help="Paper size (A3, A4, A5, Letter, Legal, etc.)"),
) -> None:
    """Roundtrip test: encode to pages, decode back, and compare."""
    if not input_file.exists():
        print_error(f"File not found: {input_file}")
        raise typer.Exit(1)

    if profile:
        config = load_profile(profile)
        if paper_size:
            from dataclasses import replace
            from common.paper_sizes import paper_size_dimensions
            w, h = paper_size_dimensions(paper_size)
            config = replace(config, page_width_mm=w, page_height_mm=h)
    else:
        config = resolve_config(config_file, num_colors, cell_size_px, paper_size)

    _execute_verification(input_file, config)
