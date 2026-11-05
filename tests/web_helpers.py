import json
import time
from pathlib import Path

import pytest
from PIL import Image
from starlette.testclient import TestClient

from web.app import create_app


def allow_printer(monkeypatch: pytest.MonkeyPatch, uri: str) -> None:
    from common.types import PrinterInfo

    found = [PrinterInfo("Test", uri, "idle", True)]
    monkeypatch.setattr("web.routes.print_routes.discover_printers", lambda: (found, uri))


def web_client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> TestClient:
    monkeypatch.chdir(tmp_path)
    return TestClient(create_app())


def small_picks() -> dict[str, object]:
    return {"paper_size": "A6", "print_dpi": 360, "cell_size_px": 18, "margin_mm": 10, "redundancy_pages": 0}


def write_print_job(root: Path, job_id: str = "job1", sides: int = 1) -> Path:
    digital = root / "data" / "print" / "jobs" / job_id / "digital"
    digital.mkdir(parents=True)
    Image.new("RGB", (12, 12), "white").save(digital / "page.png")
    meta = {
        "source_file": "note.txt", "created": "2026-01-01T00:00:00", "paper_size": "A4",
        "total_pages": 1, "data_pages": 1, "original_sha256": "abc", "prints": [], "sides": sides,
    }
    (digital.parent / "job.json").write_text(json.dumps(meta))
    return digital.parent


def wait_task(client: TestClient, task_id: str) -> dict[str, object]:
    for _ in range(400):
        body = client.get(f"/api/tasks/{task_id}").json()
        if body["state"] in ("done", "error"):
            return body
        time.sleep(0.05)
    raise AssertionError(task_id)


def upload(client: TestClient, name: str, data: bytes) -> str:
    return str(client.post("/api/inbox", files={"file": (name, data, "application/octet-stream")}).json()["file_id"])
