from pathlib import Path

import typer
from rich.console import Console

from cli.display import print_error, print_success
from common.data_store import training_pairs_dir
from common.symbols import symbol_count

console = Console()


def train_command(
    profile: str = typer.Argument(..., help="Profile name whose training data to use"),
    epochs: int = typer.Option(30, help="Maximum training epochs"),
    batch_size: int = typer.Option(128, help="Batch size"),
    cell_size: int | None = typer.Option(None, help="Cell size in pixels (auto-detected from profile)"),
) -> None:
    """Train a cell classifier model from extracted training data."""
    pairs_dir = training_pairs_dir(profile)
    tfrecord_path = pairs_dir / "cells.tfrecord"
    if not tfrecord_path.exists():
        print_error(f"No training data found at {tfrecord_path}")
        print_error("Run 'extract-training <job-id>' first.")
        raise typer.Exit(1)

    from common.config_store import load_profile
    config = load_profile(profile)
    actual_cell_size = cell_size or config.cell_size_px
    n_symbols = symbol_count(config.num_colors)

    console.print(f"[bold]Training cell classifier for profile: {profile}[/bold]")
    console.print(f"  Cell size: {actual_cell_size}px")
    console.print(f"  Symbols: {n_symbols}")
    console.print(f"  Epochs: {epochs}")
    console.print(f"  Batch: {batch_size}")
    console.print(f"  Data: {tfrecord_path}\n")

    from ml.train import train_cell_classifier
    model = train_cell_classifier(
        tfrecord_path, actual_cell_size, n_symbols, profile,
        epochs=epochs, batch_size=batch_size,
    )

    final_acc = model.history.history.get("val_accuracy", [0])[-1]
    print_success(f"Training complete. Final validation accuracy: {final_acc:.2%}")
    console.print(f"[green]Model saved to: data/models/cell_classifier/{profile}/[/green]")
