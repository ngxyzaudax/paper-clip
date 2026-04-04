from collections.abc import Callable
from pathlib import Path

import typer
from rich.console import Console

from cli.display import file_size_display, make_page_callback, make_page_progress, print_success
from common.config import ALGO_FIELDS
from common.config_store import load_profile
from common.data_store import create_job, digital_dir, update_job_metadata
from common.page_layout import data_capacity_bytes
from common.test_data import generate_test_payload, save_test_file
from serialization.encode.pipeline import encode

console = Console()


def create_test_data_job(
    profile: str, pages: int, password: str | None,
    on_page_complete: Callable[..., None] | None = None,
) -> tuple[Path, list[Path], str, str]:
    from common.config import FLAG_ENCRYPTED
    config = load_profile(profile)
    data = generate_test_payload(config, pages)
    flags = FLAG_ENCRYPTED if password else 0
    config_dict = {k: getattr(config, k) for k in ALGO_FIELDS}
    job_dir = create_job(f"testdata_{pages}p", profile, config_dict, pages)
    test_path, sha256 = save_test_file(data, job_dir)
    output_base = digital_dir(job_dir) / "page"
    png_paths = encode(
        test_path, output_base, config,
        on_page_complete=on_page_complete,
        flags=flags, passphrase=password,
    )
    update_job_metadata(job_dir, {
        "test_data": True,
        "original_sha256": sha256,
        "original_size": len(data),
    })
    return job_dir, png_paths, str(test_path), sha256


def generate_command(
    profile: str = typer.Option(..., help="Config profile name (see paper-clip config)"),
    pages: int = typer.Option(1, help="Number of pages to fill with random data"),
    password: str | None = typer.Option(None, help="Encrypt with this password"),
) -> None:
    """Generate random test data sized to fill page(s), encode, and store in a job."""
    config = load_profile(profile)
    capacity = data_capacity_bytes(config)

    console.print(f"[bold]Profile: {profile}[/bold]")
    console.print(f"  Capacity/page: {file_size_display(capacity)}")
    console.print(f"  Pages: {pages}")
    console.print(f"  Total: {file_size_display(capacity * pages)}\n")

    progress, task = make_page_progress("Rendering pages")
    with progress:
        job_dir, png_paths, test_path, sha256 = create_test_data_job(
            profile, pages, password,
            on_page_complete=make_page_callback(progress, task),
        )

    console.print(f"[cyan]Test data:  {test_path}[/cyan]")
    console.print(f"[cyan]SHA-256:    {sha256}[/cyan]")
    console.print(f"[cyan]Size:       {file_size_display(int(Path(test_path).stat().st_size))}[/cyan]\n")

    for p in png_paths:
        print_success(f"Saved {p.name}")

    console.print(f"\n[bold green]Job ready: {job_dir}[/bold green]")
    console.print("[dim]Use 'capture --job-id ...' to print+scan, then decode and verify hash.[/dim]")
