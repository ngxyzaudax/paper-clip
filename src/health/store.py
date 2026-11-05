import json
import logging
from pathlib import Path

from common.data_store import DATA_ROOT
from health.reading import Reading, Tracked, latest, tracked_from_dict, tracked_to_dict

logger = logging.getLogger(__name__)

HEALTH_DIR = DATA_ROOT / "health"
MIN_PREFIX = 4


def record_reading(sha256: str, filename: str, size: int, reading: Reading) -> Tracked:
    """Append one health reading to the file's history and return the updated history."""
    previous = load_tracked(sha256)
    name = filename or (previous.filename if previous else "")
    readings = (previous.readings if previous else ()) + (reading,)
    tracked = Tracked(sha256, name, size, readings)
    _write(tracked)
    logger.info("Recorded health %.1f%% for %s", reading.report.health, name or sha256[:12])
    return tracked


def load_tracked(sha256: str) -> Tracked | None:
    path = _path(sha256)
    return tracked_from_dict(json.loads(path.read_text())) if path.is_file() else None


def all_tracked() -> list[Tracked]:
    if not HEALTH_DIR.is_dir():
        return []
    tracked = [tracked_from_dict(json.loads(path.read_text())) for path in HEALTH_DIR.glob("*.json")]
    return sorted(tracked, key=lambda item: latest(item).time, reverse=True)


def find_tracked(query: str) -> Tracked | None:
    """Match an exact file name first, then a SHA-256 prefix of at least four hex digits."""
    wanted = query.strip().lower()
    candidates = all_tracked()
    named = [item for item in candidates if item.filename.lower() == wanted]
    if named:
        return named[0]
    prefixed = [item for item in candidates if len(wanted) >= MIN_PREFIX and item.sha256.startswith(wanted)]
    return prefixed[0] if len(prefixed) == 1 else None


def forget_tracked(sha256: str) -> bool:
    path = _path(sha256)
    if not path.is_file():
        return False
    path.unlink()
    logger.info("Removed health history for %s", sha256[:12])
    return True


def _write(tracked: Tracked) -> None:
    HEALTH_DIR.mkdir(parents=True, exist_ok=True)
    _path(tracked.sha256).write_text(json.dumps(tracked_to_dict(tracked), indent=2))


def _path(sha256: str) -> Path:
    return HEALTH_DIR / f"{sha256}.json"
