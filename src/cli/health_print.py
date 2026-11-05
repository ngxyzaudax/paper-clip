from rich.panel import Panel
from rich.table import Table

from cli.display import console
from cli.health_view import HISTORY_COLUMNS, TRACKED_COLUMNS, health_renderable, history_rows, tracked_rows
from health.check import HealthCheck
from health.reading import Tracked
from health.status import status_of


def print_health(history: Tracked, note: str) -> None:
    status = status_of(history.readings[-1].report)
    title = f"[bold]Paper health[/]  {history.filename or history.sha256[:12]}"
    console.print(Panel(health_renderable(history), title=title, subtitle=note, border_style=status.style, expand=False))


def print_check(check: HealthCheck) -> None:
    note = "saved to health history" if check.saved else "not saved, --no-track"
    print_health(check.history, f"[dim]{note}[/]")


def print_tracked(items: list[Tracked]) -> None:
    if not items:
        console.print("[dim]No files are tracked yet. Decode a scan, or run[/] paper-clip health check SCAN_JOB")
        return
    console.print(_table("Tracked files", TRACKED_COLUMNS, tracked_rows(items)))
    console.print("[dim]Details:[/] paper-clip health show NAME_OR_ID")


def print_history(history: Tracked) -> None:
    console.print(_table(f"Checks of {history.filename or history.sha256[:12]}", HISTORY_COLUMNS, history_rows(history)))


def _table(title: str, columns: tuple[str, ...], rows: list[tuple[str, ...]]) -> Table:
    table = Table(title=title, header_style="bold cyan", title_justify="left")
    for column in columns:
        table.add_column(column, overflow="fold")
    for row in rows:
        table.add_row(*row)
    return table
