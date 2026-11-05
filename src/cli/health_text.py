from datetime import datetime

from health.reading import Reading
from health.report import HealthReport
from health.status import status_of

GAUGE_WIDTH = 30


def gauge(health: float, style: str, width: int = GAUGE_WIDTH) -> str:
    filled = max(0, min(width, round(width * health / 100.0)))
    return f"[{style}]{'█' * filled}[/][grey35]{'░' * (width - filled)}[/]"


def health_value(report: HealthReport) -> str:
    status = status_of(report)
    return f"[bold {status.style}]{report.health:.1f}%[/] [{status.style}]{status.label}[/]"


def headline(report: HealthReport) -> str:
    return f"{gauge(report.health, status_of(report).style)}  {health_value(report)}"


def when(stamp: str) -> str:
    return datetime.fromisoformat(stamp).strftime("%Y-%m-%d %H:%M")


def reading_rows(reading: Reading) -> list[tuple[str, str]]:
    report = reading.report
    rows = _lost_rows(report) if report.lost else _recovered_rows(report)
    if report.header_note:
        rows.append(("Header", report.header_note))
    rows += [
        ("Pages", pages_text(report)),
        ("Reader", reading.reader),
        ("Checked", f"{when(reading.time)} from {reading.source}"),
    ]
    if reading.damage_image:
        rows.append(("Damage image", reading.damage_image))
    return rows


def _recovered_rows(report: HealthReport) -> list[tuple[str, str]]:
    share = 100.0 * report.damaged_bytes / max(1, report.payload_bytes)
    return [
        ("Repair margin", f"{report.health:.1f}% left in the weakest of {report.blocks:,} blocks, "
                          f"{report.average:.1f}% on average"),
        ("Wrong bytes", f"{report.damaged_bytes:,} of {report.payload_bytes:,} ({share:.2f}%) were misread and repaired"),
        ("Parity", f"{report.ecc_sym} of every 255 bytes"),
    ]


def _lost_rows(report: HealthReport) -> list[tuple[str, str]]:
    return [
        ("Repair margin", "[bold red]none: the damage exceeds what parity can rebuild[/]"),
        ("Parity", f"{report.ecc_sym} of every 255 bytes"),
    ]


def compact_rows(reading: Reading) -> list[tuple[str, str]]:
    report = reading.report
    if report.lost:
        rows = [("min", "[bold red]lost[/]"), ("ecc", f"{report.ecc_sym}/255")]
    else:
        share = 100.0 * report.damaged_bytes / max(1, report.payload_bytes)
        rows = [
            ("min", f"{report.health:.1f}%  {report.blocks} blk"),
            ("avg", f"{report.average:.1f}%"),
            ("damaged", f"{report.damaged_bytes:,}/{report.payload_bytes:,}  {share:.2f}%"),
            ("ecc", f"{report.ecc_sym}/255"),
        ]
    if report.header_note:
        rows.append(("header", report.header_note))
    rows += [("pages", pages_brief(report)), ("reader", reading.reader), ("checked", when(reading.time))]
    return rows


def pages_brief(report: HealthReport) -> str:
    parts = [str(len(report.pages))] if report.pages else []
    rebuilt = [str(page.index + 1) for page in report.pages if page.rebuilt]
    if rebuilt:
        parts.append("rebuilt " + ",".join(rebuilt))
    if report.missing_pages:
        parts.append("missing " + ",".join(str(index + 1) for index in report.missing_pages))
    if report.spare_pages:
        parts.append(f"spare {report.spare_pages}")
    return "  ".join(parts) or "0"


def pages_text(report: HealthReport) -> str:
    total = len(report.pages)
    rebuilt = [page.index + 1 for page in report.pages if page.rebuilt]
    parts = [f"{total} data page{'s' if total != 1 else ''}"] if total else []
    if rebuilt:
        parts.append(f"[dark_orange]rebuilt from page parity: {', '.join(map(str, rebuilt))}[/]")
    if report.missing_pages:
        parts.append(f"not scanned: {', '.join(str(index + 1) for index in report.missing_pages)}")
    if report.spare_pages:
        parts.append(f"{report.spare_pages} spare parity page{'s' if report.spare_pages != 1 else ''}")
    return ", ".join(parts) or "none read"
