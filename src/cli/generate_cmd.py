from pathlib import Path

import typer
from rich.console import Console

from cli.display import file_size_display, make_page_callback, make_page_progress, print_success
from common.config import ALGO_FIELDS
from common.config_store import load_profile
from common.data_store import create_job, digital_dir
from common.page_layout import data_capacity_bytes
from common.test_data import generate_test_payload, save_test_file
from serialization.encode.pipeline import encode

console = Console()


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

    data = generate_test_payload(config, pages)
    from common.config import FLAG_ENCRYPTED
    flags = FLAG_ENCRYPTED if password else 0

    config_dict = {k: getattr(config, k) for k in ALGO_FIELDS}
    job_dir = create_job(f"testdata_{pages}p", profile, config_dict, pages)

    test_path, sha256 = save_test_file(data, job_dir)
    console.print(f"[cyan]Test data:  {test_path}[/cyan]")
    console.print(f"[cyan]SHA-256:    {sha256}[/cyan]")
    console.print(f"[cyan]Size:       {file_size_display(len(data))}[/cyan]\n")

    output_base = digital_dir(job_dir) / "page"
    console.print("[bold]Encoding...[/bold]")
    progress, task = make_page_progress("Rendering pages")
    with progress:
        png_paths = encode(
            test_path, output_base, config,
            on_page_complete=make_page_callback(progress, task),
            flags=flags, passphrase=password,
        )

    for p in png_paths:
        print_success(f"Saved {p.name}")

    from common.data_store import update_job_metadata
    update_job_metadata(job_dir, {
        "test_data": True,
        "original_sha256": sha256,
        "original_size": len(data),
    })

    console.print(f"\n[bold green]Job ready: {job_dir}[/bold green]")
    console.print("[dim]Use 'capture --job-id ...' to print+scan, then decode and verify hash.[/dim]")
