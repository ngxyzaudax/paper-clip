import json
from pathlib import Path

from PIL import Image

from calibration.profile_diff import profile_rows
from calibration.scan_record import ScanRecord, all_reads
from calibration.session_view import session_view
from calibration.sheet_io import calibration_dir, sheet_ready
from calibration.sheet_limits import AxisLimit, ChosenProfile
from calibration.sheet_pass import patch_passed
from calibration.sheet_score import PatchRead
from calibration.sheet_session import session_records
from common.geometry_measure import mm_to_px

SHEET_DPI = 720
A4_MM = (210, 297)


def calibrate_state() -> dict[str, object]:
    view = session_view()
    records = session_records()
    return {
        "steps": [{"done": done, "label": label} for done, label in view.steps],
        "next_step": view.next_step,
        "scans": list(view.scans),
        "session_scans": [_scan(record) for record in records],
        "axes": [_axis(axis) for axis in view.axes],
        "sheet_ready": sheet_ready(),
        "profile_rows": _rows(view.chosen),
        "front_url": _sheet_url("front.png"),
        "back_url": _sheet_url("back.png"),
        "sheet_px": _sheet_px(calibration_dir() / "front.png"),
        "patches": _patches({read.name: read for read in all_reads(records)}),
    }


def _sheet_url(name: str) -> str | None:
    return f"/api/artifacts/calibration/sheet/{name}" if (calibration_dir() / name).is_file() else None


def _scan(record: ScanRecord) -> dict[str, object]:
    return {
        "name": record.name,
        "side": record.side,
        "rotation": record.rotation,
        "patches": len(record.reads),
        "url": f"/api/artifacts/calibration/session/{record.name}",
    }


def _axis(axis: AxisLimit) -> dict[str, object]:
    return {"name": axis.name, "passed": list(axis.passed), "failed": list(axis.failed), "chosen": axis.chosen}


def _rows(chosen: ChosenProfile | None) -> list[dict[str, str]] | None:
    if chosen is None:
        return None
    return [{"label": label, "now": now, "after": after} for label, now, after in profile_rows(chosen)]


def _sheet_px(front: Path) -> dict[str, int]:
    if not front.is_file():
        return {"w": mm_to_px(A4_MM[0], SHEET_DPI), "h": mm_to_px(A4_MM[1], SHEET_DPI)}
    with Image.open(front) as image:
        return {"w": image.width, "h": image.height}


def _patches(reads: dict[str, PatchRead]) -> dict[str, list[dict[str, object]]]:
    layout = _layout()
    return {name: _side(layout, name, reads) for name in ("front", "back")}


def _layout() -> list[object]:
    path = calibration_dir() / "layout.json"
    if not path.is_file():
        return []
    return _as_list(json.loads(path.read_text()))


def _as_list(value: object) -> list[object]:
    if isinstance(value, list):
        return list(value)
    return []


def _side(sides: list[object], name: str, reads: dict[str, PatchRead]) -> list[dict[str, object]]:
    found = [item for item in (_object_dict(side) for side in sides) if item is not None and item.get("side") == name]
    return [_patch(item, reads.get(str(item.get("name")))) for item in _patch_items(found)]


def _patch_items(found: list[dict[str, object]]) -> list[dict[str, object]]:
    if not found:
        return []
    return [item for item in (_object_dict(patch) for patch in _as_list(found[0].get("patches", []))) if item is not None]


def _object_dict(value: object) -> dict[str, object] | None:
    if not isinstance(value, dict):
        return None
    return {str(key): item for key, item in value.items()}


def _patch(item: dict[str, object], read: PatchRead | None) -> dict[str, object]:
    return {
        "name": str(item.get("name", "")),
        "x": _mm(item, "x_mm"),
        "y": _mm(item, "y_mm"),
        "w": _mm(item, "w_mm"),
        "h": _mm(item, "h_mm"),
        "read": read is not None,
        "passed": bool(read and patch_passed(read)),
    }


def _mm(item: dict[str, object], key: str) -> int:
    return mm_to_px(float(str(item.get(key, 0))), SHEET_DPI)
