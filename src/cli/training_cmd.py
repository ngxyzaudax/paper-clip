from pathlib import Path

import typer
from rich.console import Console

from cli.display import print_error, print_success
from common.data_store import find_job, load_job_metadata, training_pairs_dir

console = Console()


def _config_from_meta(meta: dict) -> "PaperClipConfig":
    from common.config import PaperClipConfig, validate_config
    cfg = meta.get("config", {})
    valid_fields = {f.name for f in __import__("dataclasses").fields(PaperClipConfig)}
    filtered = {k: v for k, v in cfg.items() if k in valid_fields}
    return validate_config(PaperClipConfig(**filtered))


def extract_training_command(
    job_id: str = typer.Argument(..., help="Job ID prefix to extract training data from"),
) -> None:
    """Extract cell crops from a capture job into TFRecord training data."""
    job_dir = find_job(job_id)
    if not job_dir:
        print_error(f"No job found matching: {job_id}")
        raise typer.Exit(1)

    meta = load_job_metadata(job_dir)
    profile = meta.get("profile", "unknown")
    config = _config_from_meta(meta)

    console.print(f"[cyan]Job: {job_dir.name}[/cyan]")
    console.print(f"[cyan]Profile: {profile}[/cyan]")
    console.print(f"[cyan]Config: {config.num_colors}c cell={config.cell_size_px}px[/cyan]\n")

    console.print("[bold]Extracting cell pairs...[/bold]")
    from ml.extract_pairs import extract_job_pairs
    crops, labels = extract_job_pairs(job_dir, config)

    if len(labels) == 0:
        print_error("No cell pairs extracted. Ensure capture is complete with master scans.")
        raise typer.Exit(1)

    console.print(f"  Extracted {len(labels):,} cells")
    unique, counts = __import__("numpy").unique(labels, return_counts=True)
    for sym, cnt in zip(unique, counts):
        console.print(f"    Symbol {sym}: {cnt:,} ({cnt / len(labels) * 100:.1f}%)")

    output_dir = training_pairs_dir(profile)
    output_file = output_dir / "cells.tfrecord"
    console.print(f"\n[bold]Writing TFRecord to {output_file}...[/bold]")

    from ml.dataset import write_tfrecord
    n = write_tfrecord(crops, labels, output_file)
    print_success(f"Wrote {n:,} training examples to {output_file}")
