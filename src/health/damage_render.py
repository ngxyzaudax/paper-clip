from pathlib import Path
from typing import NamedTuple

import numpy as np
from PIL import Image

from health.damage_overlay import page_overlay
from health.damage_sheet import damage_sheet
from health.report import HealthReport
from health.status import status_of
from health import store
from health.wrong_cells import NO_CELLS
from serialization.decode.observe import PageObservation

DAMAGE_FOLDER = "damage"


class DamageImages(NamedTuple):
    sheet: Path
    pages: tuple[Path, ...]


def save_damage_image(
    sha256: str,
    filename: str,
    stamp: str,
    report: HealthReport,
    observed: tuple[PageObservation, ...],
    wrong: tuple[np.ndarray, ...],
) -> DamageImages | None:
    """Write one image showing where on the paper the damage sits; None when no page was read."""
    if not observed:
        return None
    panels = [
        (page_overlay(page, _wrong(wrong, position)), _caption(page, report)) for position, page in enumerate(observed)
    ]
    sheet = damage_sheet(_title(filename, report), _subtitle(stamp, report), panels)
    path = store.HEALTH_DIR / DAMAGE_FOLDER / sha256[:16] / f"{stamp.replace(':', '')}.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(path, optimize=True)
    return DamageImages(path, _save_panels(path, panels))


def _save_panels(sheet: Path, panels: list[tuple[Image.Image, str]]) -> tuple[Path, ...]:
    folder = sheet.with_suffix("")
    folder.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for position, (panel, _caption) in enumerate(panels):
        path = folder / f"page_{position + 1:02d}.png"
        panel.save(path, optimize=True)
        paths.append(path)
    return tuple(paths)


def _wrong(wrong: tuple[np.ndarray, ...], position: int) -> np.ndarray:
    return wrong[position] if position < len(wrong) else NO_CELLS


def _title(filename: str, report: HealthReport) -> str:
    status = status_of(report)
    return f"{filename or 'Unknown file'}   health {report.health:.1f}%   {status.label}"


def _subtitle(stamp: str, report: HealthReport) -> str:
    damaged = f"{report.damaged_bytes:,} of {report.payload_bytes:,} bytes were wrong"
    return f"Checked {stamp.replace('T', ' ')[:16]}   {damaged}   {report.ecc_sym} parity bytes per block"


def _caption(page: PageObservation, report: HealthReport) -> str:
    index = page.header.page_index
    side = f"Page {index + 1} of {page.header.total_pages}"
    if index >= page.header.data_pages:
        return f"{side}   page parity"
    match = [item for item in report.pages if item.index == index]
    if not match:
        return f"{side}   not readable"
    health = match[0]
    if health.rebuilt:
        return f"{side}   rebuilt from page parity"
    return f"{side}   {health.damaged:,} wrong bytes ({100.0 * health.damaged / max(1, health.size):.2f}%)"
