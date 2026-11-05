from typing import NamedTuple

from health.report import HealthReport

REPRINT_THRESHOLD = 35.0


class Status(NamedTuple):
    label: str
    style: str
    advice: str


HEALTHY = Status(
    "Healthy", "green",
    "Plenty of repair margin left. Re-check about once a year, or after the paper was handled, moved, or got damp.",
)
WORN = Status(
    "Worn", "yellow",
    "The paper copy is still readable. You do not need a new print yet. Check again in a few months, and print a fresh copy before this falls under 35%. Keep the sheets flat, dark, and dry.",
)
AT_RISK = Status(
    "At risk", "dark_orange",
    "Print a fresh copy soon. Most of the spare repair data is already in use.",
)
CRITICAL = Status(
    "Critical", "red",
    "The file only just survived. Keep the recovered file and print a new copy today.",
)
LOST = Status(
    "Lost", "bold red",
    "The pages no longer hold enough data to rebuild the file. Try a cleaner rescan, then fall back to another copy.",
)

_BANDS = ((60.0, HEALTHY), (REPRINT_THRESHOLD, WORN), (15.0, AT_RISK), (0.0, CRITICAL))


def status_of(report: HealthReport) -> Status:
    if report.lost:
        return LOST
    band = next(status for floor, status in _BANDS if report.health >= floor)
    return AT_RISK if band in (HEALTHY, WORN) and _rebuilt(report) else band


def _rebuilt(report: HealthReport) -> bool:
    return any(page.rebuilt for page in report.pages)
