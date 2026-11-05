from typing import Any, NamedTuple

from health.pages import PageHealth
from health.report import HealthReport


class Reading(NamedTuple):
    time: str
    source: str
    reader: str
    report: HealthReport
    damage_image: str = ""
    damage_pages: tuple[str, ...] = ()


class Tracked(NamedTuple):
    sha256: str
    filename: str
    size: int
    readings: tuple[Reading, ...]


def latest(tracked: Tracked) -> Reading:
    return tracked.readings[-1]


def tracked_to_dict(tracked: Tracked) -> dict[str, Any]:
    return {
        "sha256": tracked.sha256,
        "filename": tracked.filename,
        "size": tracked.size,
        "readings": [_reading_to_dict(reading) for reading in tracked.readings],
    }


def tracked_from_dict(data: dict[str, Any]) -> Tracked:
    return Tracked(
        str(data["sha256"]),
        str(data["filename"]),
        int(data["size"]),
        tuple(_reading_from_dict(item) for item in data["readings"]),
    )


def _reading_to_dict(reading: Reading) -> dict[str, Any]:
    report = reading.report._asdict()
    report["pages"] = [page._asdict() for page in reading.report.pages]
    return {
        "time": reading.time,
        "source": reading.source,
        "reader": reading.reader,
        "report": report,
        "damage_image": reading.damage_image,
        "damage_pages": list(reading.damage_pages),
    }


def _reading_from_dict(data: dict[str, Any]) -> Reading:
    return Reading(
        str(data["time"]),
        str(data["source"]),
        str(data["reader"]),
        _report_from_dict(data["report"]),
        str(data["damage_image"]),
        tuple(str(item) for item in data.get("damage_pages", ())),
    )


def _report_from_dict(data: dict[str, Any]) -> HealthReport:
    fields = {**data, "pages": tuple(_page_from_dict(page) for page in data["pages"])}
    fields["missing_pages"] = tuple(data["missing_pages"])
    fields.setdefault("header_note", "")
    return HealthReport(**fields)


def _page_from_dict(data: dict[str, Any]) -> PageHealth:
    damage = tuple(tuple(float(value) for value in row) for row in data["damage_map"])
    return PageHealth(int(data["index"]), int(data["damaged"]), int(data["size"]), bool(data["rebuilt"]), damage)
