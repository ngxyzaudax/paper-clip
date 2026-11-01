from textual.widget import Widget
from textual.widgets import DataTable, Static

from calibration.profile_diff import profile_rows
from calibration.session_view import SessionView, format_steps

LIMIT_COLUMNS = ("Aspect", "Chosen", "Passed", "Failed")


def apply_session_view(screen: Widget, view: SessionView) -> None:
    """Fill the calibration panel widgets from a freshly computed session view."""
    screen.query_one("#cal-steps", Static).update(format_steps(view.steps))
    screen.query_one("#cal-next", Static).update(view.next_step)
    screen.query_one("#cal-scans", Static).update(_scans_text(view.scans))
    _fill_table(screen.query_one("#cal-table", DataTable), view)
    screen.query_one("#cal-summary", Static).update(_summary(view))


def _fill_table(table: DataTable, view: SessionView) -> None:
    table.clear(columns=True)
    table.add_columns(*LIMIT_COLUMNS)
    for axis in view.axes:
        table.add_row(axis.name, axis.chosen, _joined(axis.passed), _joined(axis.failed))


def _summary(view: SessionView) -> str:
    if view.chosen is None:
        return "No scans have been read yet. The table fills in after the first scan."
    rows = profile_rows(view.chosen)
    return "\n".join(f"{label}: {now} -> {after}" for label, now, after in rows)


def _scans_text(scans: tuple[str, ...]) -> str:
    return "\n".join(scans) if scans else "No scans in this session."


def _joined(values: tuple[str, ...]) -> str:
    return ", ".join(values) if values else "-"
