from datetime import datetime, timedelta
from typing import NamedTuple

from health.reading import Reading, Tracked
from health.status import REPRINT_THRESHOLD

MIN_SPAN_DAYS = 1.0
DAYS_PER_YEAR = 365.25
MAX_PROJECTION_DAYS = DAYS_PER_YEAR * 200


class Trend(NamedTuple):
    since_previous: float | None
    since_first: float | None
    per_year: float | None
    target: float | None
    reaches_target: datetime | None


def now_stamp() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def trend_of(tracked: Tracked) -> Trend:
    """Change in health between readings and, once readings span a day, a straight-line projection."""
    readings = tracked.readings
    current = readings[-1].report.health
    since_previous = _delta(readings[-2], readings[-1]) if len(readings) > 1 else None
    since_first = _delta(readings[0], readings[-1]) if len(readings) > 1 else None
    per_day = _slope_per_day(readings)
    per_year = per_day * DAYS_PER_YEAR if per_day is not None else None
    target = REPRINT_THRESHOLD if current > REPRINT_THRESHOLD else 0.0
    return Trend(since_previous, since_first, per_year, target, _reaches(readings[-1], per_day, target))


def _delta(earlier: Reading, later: Reading) -> float:
    return round(later.report.health - earlier.report.health, 1)


def _slope_per_day(readings: tuple[Reading, ...]) -> float | None:
    days = [_days_since(readings[0], reading) for reading in readings]
    if len(readings) < 2 or days[-1] - days[0] < MIN_SPAN_DAYS:
        return None
    values = [reading.report.health for reading in readings]
    mean_day = sum(days) / len(days)
    mean_value = sum(values) / len(values)
    spread = sum((day - mean_day) ** 2 for day in days)
    covariance = sum((day - mean_day) * (value - mean_value) for day, value in zip(days, values))
    return covariance / spread if spread else None


def _reaches(last: Reading, per_day: float | None, target: float) -> datetime | None:
    if per_day is None or per_day >= 0 or last.report.lost:
        return None
    days = (last.report.health - target) / -per_day
    return parse_time(last.time) + timedelta(days=days) if days < MAX_PROJECTION_DAYS else None


def _days_since(first: Reading, reading: Reading) -> float:
    return (parse_time(reading.time) - parse_time(first.time)).total_seconds() / 86400.0


def parse_time(stamp: str) -> datetime:
    return datetime.fromisoformat(stamp)
