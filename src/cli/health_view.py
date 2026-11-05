from rich.console import Group, RenderableType
from rich.table import Table
from rich.text import Text

from cli.health_map_text import map_lines
from cli.health_text import compact_rows, headline, health_value, reading_rows, when
from cli.health_trend_text import change_text, compact_trend_rows, trend_rows
from health.reading import Tracked, latest
from health.status import status_of
from health.trend import trend_of

TRACKED_COLUMNS = ("File", "Health", "Change", "Checks", "Last check", "ID")
HISTORY_COLUMNS = ("Checked", "Health", "Change", "Wrong bytes", "Reader", "Scan")


def compact_health(history: Tracked) -> Group:
    """Gauge, RS margin, header, and the zone map."""
    reading = latest(history)
    parts: list[RenderableType] = [Text.from_markup(headline(reading.report))]
    parts.append(_facts([*compact_rows(reading), *compact_trend_rows(history)]))
    zones = map_lines(reading.report)
    if zones:
        parts += [Text(""), *(Text.from_markup(line) for line in zones)]
    return Group(*parts)


def health_renderable(history: Tracked) -> Group:
    """Everything known about one file's paper: current health, facts, trend, advice, and where the damage is."""
    reading = latest(history)
    parts: list[RenderableType] = [Text.from_markup(headline(reading.report)), Text("")]
    parts.append(_facts([*reading_rows(reading), *trend_rows(history)]))
    zones = map_lines(reading.report)
    if zones:
        parts += [Text(""), Text.from_markup("[bold]Where the damage is[/]"), *map(Text.from_markup, zones)]
    return Group(*parts)


def _facts(rows: list[tuple[str, str]]) -> Table:
    grid = Table.grid(padding=(0, 2))
    grid.add_column(style="bold", no_wrap=True)
    grid.add_column(overflow="fold")
    for label, value in rows:
        grid.add_row(label, Text.from_markup(value))
    return grid


def tracked_rows(items: list[Tracked]) -> list[tuple[str, ...]]:
    return [_tracked_row(item) for item in items]


def _tracked_row(item: Tracked) -> tuple[str, ...]:
    reading = latest(item)
    return (
        item.filename or "[dim]unknown name[/]",
        health_value(reading.report),
        change_text(trend_of(item).since_previous),
        str(len(item.readings)),
        when(reading.time),
        item.sha256[:12],
    )


def history_rows(item: Tracked) -> list[tuple[str, ...]]:
    readings = item.readings
    rows = []
    for position, reading in enumerate(readings):
        previous = readings[position - 1].report.health if position else None
        delta = None if previous is None else round(reading.report.health - previous, 1)
        rows.append((
            when(reading.time),
            health_value(reading.report),
            change_text(delta),
            "lost" if reading.report.lost else f"{reading.report.damaged_bytes:,}",
            reading.reader,
            reading.source,
        ))
    return list(reversed(rows))


def alert_text(items: list[Tracked]) -> str:
    """One line naming the files whose paper needs attention, or an empty string when all are fine."""
    flagged = [item for item in items if status_of(latest(item).report).label not in ("Healthy", "Worn")]
    if not flagged:
        return ""
    names = ", ".join(item.filename or item.sha256[:12] for item in flagged[:3])
    more = f" +{len(flagged) - 3}" if len(flagged) > 3 else ""
    return f"{len(flagged)} below 35%: {names}{more}"
