import hashlib
import json
from pathlib import Path

from calibration.sheet_draw import draw_side
from calibration.sheet_place import sheet_side
from calibration.sheet_spec import Patch


def calibration_dir() -> Path:
    return Path("data") / "calibration"


def session_dir() -> Path:
    return calibration_dir() / "session"


def layout_fingerprint() -> str:
    text = json.dumps(layout_manifest(), sort_keys=True)
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def sheet_ready(directory: Path | None = None) -> bool:
    target = directory or calibration_dir()
    return all((target / name).exists() for name in ("front.png", "back.png", "layout.json"))


def layout_manifest() -> list[dict[str, object]]:
    return [
        {"side": name, "patches": [_patch_row(patch) for patch in sheet_side(name).patches]}
        for name in ("front", "back")
    ]


def write_sheet(directory: Path | None = None, dpi: int = 720) -> Path:
    target = directory or calibration_dir()
    target.mkdir(parents=True, exist_ok=True)
    for name in ("front", "back"):
        image = draw_side(sheet_side(name), dpi)
        image.save(target / f"{name}.png", format="PNG", compress_level=1, dpi=(dpi, dpi))
    (target / "layout.json").write_text(json.dumps(layout_manifest(), indent=2))
    return target


def _patch_row(patch: Patch) -> dict[str, object]:
    return {
        "kind": patch.kind,
        "name": patch.name,
        "x_mm": round(patch.x_mm, 2),
        "y_mm": round(patch.y_mm, 2),
        "w_mm": round(patch.w_mm, 2),
        "h_mm": round(patch.h_mm, 2),
        "qr_mm": patch.qr_mm,
        "tag_mm": patch.tag_mm,
        "pitch_mm": patch.pitch_mm,
        "cell_px": patch.cell_px,
        "dot_ratio": patch.dot_ratio,
        "symbols": patch.symbols,
        "tag_ids": list(patch.tag_ids),
    }
