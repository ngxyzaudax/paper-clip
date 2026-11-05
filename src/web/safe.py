from pathlib import Path

from common.data_store import DATA_ROOT


def under_data(path: Path) -> Path:
    root = DATA_ROOT.resolve()
    resolved = path.resolve()
    resolved.relative_to(root)
    return resolved


def safe_segment(value: str) -> str:
    if not value or value in (".", "..") or "/" in value or "\\" in value:
        raise ValueError("invalid path")
    return value
