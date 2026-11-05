import json
import os
import threading
import uuid
from collections.abc import Callable
from pathlib import Path

JsonObject = dict[str, object]

_locks: dict[Path, threading.Lock] = {}
_locks_guard = threading.Lock()


class JsonFileError(ValueError):
    """Raised when a JSON metadata file exists but cannot be parsed into an object."""


def read_json_object(path: Path) -> JsonObject:
    """Return the JSON object stored at path, an empty object when the file is absent."""
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError) as exc:
        raise JsonFileError(f"Unreadable JSON metadata: {path.name}") from exc
    if not isinstance(data, dict):
        raise JsonFileError(f"JSON metadata is not an object: {path.name}")
    return data


def write_json_atomic(path: Path, data: JsonObject) -> None:
    """Write data to path through a temporary file and an atomic replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(f"{path.name}.{uuid.uuid4().hex}.part")
    partial.write_text(json.dumps(data, indent=2))
    os.replace(partial, path)


def update_json_object(path: Path, change: Callable[[JsonObject], JsonObject]) -> JsonObject:
    """Read, transform, and atomically rewrite the object at path under a per-file lock."""
    with _lock_for(path):
        updated = change(read_json_object(path))
        write_json_atomic(path, updated)
        return updated


def _lock_for(path: Path) -> threading.Lock:
    key = path.resolve()
    with _locks_guard:
        return _locks.setdefault(key, threading.Lock())
