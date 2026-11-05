from cli.health_text import when
from health.reading import Tracked
from health.status import status_of
from health.trend import Trend, trend_of

STEADY_POINTS = 0.5


def change_text(delta: float | None) -> str:
    if delta is None:
        return "[dim]first check[/]"
    if abs(delta) < STEADY_POINTS:
        return f"[green]steady ({delta:+.1f})[/]"
    style = "red" if delta < 0 else "green"
    return f"[{style}]{delta:+.1f} points[/]"


def compact_trend_rows(history: Tracked) -> list[tuple[str, str]]:
    trend = trend_of(history)
    readings = history.readings
    rows: list[tuple[str, str]] = []
    if trend.since_previous is not None:
        rows.append(("Δ", f"{_delta(trend.since_previous)}  {when(readings[-2].time)}"))
    if len(readings) > 2:
        rows.append(("Δ0", f"{_delta(trend.since_first)}  n={len(readings)}"))
    if trend.per_year is not None:
        rows.append(("Δ/yr", _delta(trend.per_year)))
    if trend.reaches_target is not None and trend.target is not None:
        rows.append(("t*", f"{trend.reaches_target:%Y-%m-%d}  {trend.target:.0f}%"))
    return rows


def _delta(delta: float | None) -> str:
    if delta is None:
        return "[dim]—[/]"
    style = "green" if delta >= 0 else "red"
    return f"[{style}]{delta:+.1f}[/]"


def trend_rows(history: Tracked) -> list[tuple[str, str]]:
    trend = trend_of(history)
    readings = history.readings
    rows = [("Since last", _since_last(trend, history))]
    if len(readings) > 2:
        rows.append(("Since first", f"{change_text(trend.since_first)} over {len(readings)} checks "
                                    f"from {when(readings[0].time)}"))
    rows += _rate_rows(trend)
    rows.append(("Advice", status_of(readings[-1].report).advice))
    return rows


def _since_last(trend: Trend, history: Tracked) -> str:
    if trend.since_previous is None:
        return "[dim]first check of this file, the next one will show how fast it changes[/]"
    return f"{change_text(trend.since_previous)} since {when(history.readings[-2].time)}"


def _rate_rows(trend: Trend) -> list[tuple[str, str]]:
    if trend.per_year is None:
        return []
    rows = [("Rate", f"{change_text(trend.per_year)} per year")]
    if trend.reaches_target is not None and trend.target is not None:
        label = "reprint level" if trend.target > 0 else "data loss"
        rows.append(("Forecast", f"[bold]{trend.reaches_target:%Y-%m-%d}[/] reaches {label} "
                                 f"({trend.target:.0f}%) at this rate"))
    return rows
