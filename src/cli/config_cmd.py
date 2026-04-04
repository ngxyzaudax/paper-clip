from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from cli.display import config_table, print_success
from common.config import PaperClipConfig, default_config, load_config, save_config
from common.config_store import list_profiles, save_profile
from common.page_layout import data_capacity_bytes, grid_dimensions
from common.symbols import bits_per_cell, symbol_count

console = Console()


def _config_to_rows(config: PaperClipConfig) -> list[tuple[str, str]]:
    return [
        ("num_colors", str(config.num_colors)),
        ("cell_size_px", str(config.cell_size_px)),
        ("scan_dpi", str(config.scan_dpi)),
        ("rs_redundancy", str(config.rs_redundancy)),
    ]


def _show_derived_stats(config: PaperClipConfig) -> None:
    cols, rows = grid_dimensions(config)
    bpc = bits_per_cell(config.num_colors)
    sc = symbol_count(config.num_colors)
    capacity = data_capacity_bytes(config)

    table = Table(title="Derived Properties", show_header=True, header_style="bold cyan")
    table.add_column("Property", style="bold")
    table.add_column("Value")
    table.add_row("Symbol count", str(sc))
    table.add_row("Bits per cell", f"{bpc:.2f}")
    table.add_row("Grid size", f"{cols} x {rows}")
    table.add_row("Total cells", f"{cols * rows:,}")
    table.add_row("Capacity/page", f"{capacity:,} bytes ({capacity / 1024:.1f} KB)")
    console.print(table)


def config_command(
    list_all: bool = typer.Option(False, "--list", "-l", help="List available profiles"),
    show: Path | None = typer.Option(None, help="Show config from a TOML file"),
    output: Path | None = typer.Option(None, help="Save default config to this path"),
) -> None:
    """Manage paper-clip configuration profiles."""
    if list_all:
        profiles = list_profiles()
        table = Table(title="Available Profiles", show_header=True, header_style="bold cyan")
        table.add_column("Name", style="bold")
        table.add_column("Path", style="dim")
        for name, path in profiles:
            table.add_row(name, str(path))
        console.print(table)
    elif show:
        if not show.exists():
            console.print(f"[red]Config file not found: {show}[/red]")
            raise typer.Exit(1)
        config = load_config(show)
        config_table(_config_to_rows(config))
        _show_derived_stats(config)
    elif output:
        config = default_config()
        save_config(config, output)
        print_success(f"Default config saved to {output}")
        config_table(_config_to_rows(config))
    else:
        config = default_config()
        console.print("[bold]Default configuration:[/bold]")
        config_table(_config_to_rows(config))
        _show_derived_stats(config)
