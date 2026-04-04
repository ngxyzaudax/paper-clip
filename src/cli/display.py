from collections.abc import Callable
from pathlib import Path

from rich.console import Console
from rich.progress import BarColumn, Progress, TaskProgressColumn, TextColumn, TimeRemainingColumn
from rich.table import Table

console = Console()


def file_size_display(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.2f} MB"


def config_table(rows: list[tuple[str, str]], title: str = "Configuration") -> None:
    table = Table(title=title, show_header=True, header_style="bold cyan")
    table.add_column("Setting", style="bold")
    table.add_column("Value", style="white")
    for label, value in rows:
        table.add_row(label, value)
    console.print(table)


def print_success(message: str) -> None:
    console.print(f"\n[bold green]{message}[/bold green]")


def print_error(message: str) -> None:
    console.print(f"\n[bold red]{message}[/bold red]")


def make_page_progress(description: str, total: int | None = None) -> tuple[Progress, int]:
    progress = Progress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=40),
        TaskProgressColumn(),
        TimeRemainingColumn(),
        console=console,
    )
    task = progress.add_task(description, total=total)
    return progress, task


def make_page_callback(progress: Progress, task_id: int) -> Callable[[int, int, Path], None]:
    def on_page(idx: int, total: int, path: Path) -> None:
        if progress.tasks[task_id].total is None:
            progress.update(task_id, total=total)
        progress.advance(task_id)
    return on_page
