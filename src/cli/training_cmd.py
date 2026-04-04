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


def extract_training_data(job_id: str) -> tuple[Path, int, str]:
    job_dir = find_job(job_id)
    if not job_dir:
        raise ValueError(f"No job found matching: {job_id}")

    meta = load_job_metadata(job_dir)
    profile = meta.get("profile", "unknown")
    config = _config_from_meta(meta)

    from ml.extract_pairs import extract_job_pairs
    crops, labels = extract_job_pairs(job_dir, config)

    if len(labels) == 0:
        raise ValueError("No cell pairs extracted. Ensure capture is complete with master scans.")

    lines = [f"Extracted {len(labels):,} cells"]
    unique, counts = __import__("numpy").unique(labels, return_counts=True)
    for sym, cnt in zip(unique, counts):
        lines.append(f"  Symbol {sym}: {cnt:,} ({cnt / len(labels) * 100:.1f}%)")

    output_dir = training_pairs_dir(profile)
    output_file = output_dir / "cells.tfrecord"

    from ml.dataset import write_tfrecord
    n = write_tfrecord(crops, labels, output_file)
    summary = "\n".join(lines)
    return output_file, n, summary


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

    try:
        output_file, n, summary = extract_training_data(job_id)
    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)

    for line in summary.split("\n"):
        console.print(f"  {line}")
    console.print(f"\n[bold]TFRecord: {output_file}[/bold]")
    print_success(f"Wrote {n:,} training examples to {output_file}")
