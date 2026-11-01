import json
from datetime import datetime
from pathlib import Path

from calibration.sheet_io import calibration_dir


def note_print(job_ids: list[int], sides: str) -> None:
    payload = {"job_ids": job_ids, "sides": sides, "time": datetime.now().isoformat(timespec="seconds")}
    _path("print.json").write_text(json.dumps(payload, indent=2))


def print_note() -> str | None:
    path = _path("print.json")
    if not path.exists():
        return None
    try:
        raw = json.loads(path.read_text())
        ids = ", ".join(str(job_id) for job_id in raw["job_ids"])
        return f"job {ids}, {raw['sides']}, {raw['time'].replace('T', ' ')}"
    except (OSError, ValueError, KeyError, TypeError):
        return None


def save_simulation(text: str) -> None:
    _path("simulation.txt").write_text(text)


def simulation_text() -> str | None:
    path = _path("simulation.txt")
    return path.read_text() if path.exists() else None


def _path(name: str) -> Path:
    folder = calibration_dir()
    folder.mkdir(parents=True, exist_ok=True)
    return folder / name
