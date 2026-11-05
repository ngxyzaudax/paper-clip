from collections.abc import Iterable
from pathlib import Path

from common.data_store import DATA_ROOT
from health.pages import PageHealth
from health.reading import Reading, Tracked, latest
from health.status import status_of
from health.trend import trend_of
from workflows.print_jobs import PrintJob


def print_summary(job: PrintJob) -> dict[str, object]:
    duplex = bool(job.prints[-1].get("duplex")) if job.prints else job.sides == 2
    return {
        "job_id": job.job_id,
        "source_file": job.source_file,
        "created": job.created,
        "paper_size": job.paper_size,
        "pages": len(job.page_paths),
        "data_pages": job.data_pages,
        "total_pages": job.total_pages or len(job.page_paths),
        "original_sha256": job.original_sha256,
        "duplex": duplex,
        "sides": job.sides,
        "printed": len(job.prints),
        "page_names": [path.name for path in job.page_paths],
    }


def health_row(item: Tracked) -> dict[str, object]:
    reading = latest(item)
    status = status_of(reading.report)
    trend = trend_of(item)
    return {
        "sha256": item.sha256,
        "filename": item.filename,
        "health": reading.report.health,
        "status": status.label,
        "change": trend.since_previous,
        "checks": len(item.readings),
        "time": reading.time,
    }


def health_detail(item: Tracked) -> dict[str, object]:
    trend = trend_of(item)
    return {
        "sha256": item.sha256,
        "filename": item.filename,
        "size": item.size,
        "trend": {
            "since_previous": trend.since_previous,
            "since_first": trend.since_first,
            "per_year": trend.per_year,
            "reaches_target": trend.reaches_target.isoformat() if trend.reaches_target else None,
        },
        "readings": [reading_json(reading) for reading in item.readings],
    }


def reading_json(reading: Reading) -> dict[str, object]:
    report = reading.report
    status = status_of(report)
    return {
        "time": reading.time,
        "health": report.health,
        "status": status.label,
        "advice": status.advice,
        "reader": reading.reader,
        "damaged_bytes": report.damaged_bytes,
        "payload_bytes": report.payload_bytes,
        "missing_pages": list(report.missing_pages),
        "lost": report.lost,
        "pages": [_page(page) for page in report.pages],
        "damage_pages": media_urls([*reading.damage_pages, reading.damage_image]),
    }


def media_urls(stored: Iterable[str]) -> list[str]:
    """Return media URLs for the stored damage images that live under the damage root."""
    return [url for url in (media_url(path) for path in stored if path) if url]


def media_url(stored: str) -> str:
    """Return the media URL of one damage image, or an empty string when it lies outside the damage root."""
    root = (DATA_ROOT / "health" / "damage").resolve()
    resolved = Path(stored).resolve()
    if not resolved.is_relative_to(root):
        return ""
    return "/api/media/damage/" + "/".join(resolved.relative_to(root).parts)


def _page(page: PageHealth) -> dict[str, object]:
    return {
        "index": page.index,
        "damaged": page.damaged,
        "rebuilt": page.rebuilt,
        "damage_map": [list(row) for row in page.damage_map],
    }
