import json
import time
from pathlib import Path

import pytest
from starlette.testclient import TestClient
from PIL import Image

from web.app import create_app
from web_helpers import allow_printer, small_picks, wait_task, web_client, write_print_job


def test_home_library_and_options_start_empty(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    client = web_client(monkeypatch, tmp_path)
    home = client.get("/api/home")
    assert home.status_code == 200
    assert home.json()["newest_print"] is None
    assert client.get("/api/library").json() == {"documents": [], "unlinked": []}
    options = client.get("/api/encode/options").json()
    assert options["fields"]
    assert "margin_mm" in options["defaults"]
    assert client.get("/api/health").json() == []
    assert client.delete("/api/health/missing").status_code == 400


def test_remote_host_requires_the_printed_token(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    client = TestClient(create_app(token="secret-token"))
    assert client.get("/api/home").status_code == 401
    allowed = client.get("/api/home", headers={"Authorization": "Bearer secret-token"})
    assert allowed.status_code == 200


def test_print_and_calibrate_require_confirm(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    client = web_client(monkeypatch, tmp_path)
    write_print_job(tmp_path)
    allow_printer(monkeypatch, "ipp://printer.test/ipp/print")
    monkeypatch.setattr("workflows.print_submit.print_pages", lambda *_args, **_kwargs: [4])
    denied = client.post("/api/print/jobs/job1", json={"printer": "ipp://printer.test/ipp/print"})
    assert denied.status_code == 400
    started = client.post("/api/print/jobs/job1", json={"printer": "ipp://printer.test/ipp/print", "confirm": True})
    finished = wait_task(client, started.json()["task_id"])
    assert finished["state"] == "done", finished
    saved = json.loads((tmp_path / "data" / "print" / "jobs" / "job1" / "job.json").read_text())
    assert saved["prints"][0]["duplex"] is False
    assert client.post("/api/calibrate/print").status_code == 400
    assert client.post("/api/calibrate/save", json={}).status_code == 400
    assert client.post("/api/calibrate/new", json={"confirm": False}).status_code == 400
    state = client.get("/api/calibrate")
    assert state.status_code == 200
    assert state.json()["steps"]


def test_files_reject_traversal_and_active_html(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    client = web_client(monkeypatch, tmp_path)
    write_print_job(tmp_path)
    escaped = client.get("/api/artifacts/print/%2e%2e/page.png")
    assert escaped.status_code == 400
    upload = client.post("/api/inbox", files={"file": ("page.html", b"<html><script>bad()</script></html>", "text/html")})
    file_id = upload.json()["file_id"]
    served = client.get(f"/api/files/inbox/{file_id}")
    assert served.headers["content-type"].startswith("text/plain")
    assert served.headers["x-content-type-options"] == "nosniff"
    assert "sandbox" in served.headers["content-security-policy"]
    crop = client.get("/api/artifacts/print/job1/page.png/crop?x=0&y=0&w=4&h=4")
    assert crop.status_code == 200
    assert crop.content.startswith(b"\xff\xd8")


def test_encode_job_omits_the_passphrase(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    client = web_client(monkeypatch, tmp_path)
    upload = client.post("/api/inbox", files={"file": ("note.txt", b"hello paper", "text/plain")})
    file_id = upload.json()["file_id"]
    preview = client.post("/api/encode/preview", json={"file_id": file_id, "picks": small_picks(), "page": 0, "passphrase": "hunter2"})
    assert preview.status_code == 200, preview.text
    body = preview.json()
    assert body["geometry"]["page"]["w"] > 0
    assert client.get(body["image"]).status_code == 200
    started = client.post("/api/encode", json={"file_id": file_id, "preview_id": body["preview_id"], "picks": small_picks(), "passphrase": "hunter2"})
    finished = wait_task(client, started.json()["task_id"])
    assert finished["state"] == "done", finished
    job_id = finished["result"]["job_id"]
    text = (tmp_path / "data" / "print" / "jobs" / job_id / "job.json").read_text()
    assert "hunter2" not in text
    assert "passphrase" not in text
    assert json.loads(text)["original_sha256"]


def test_wizard_names_the_next_duplex_side(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    client = web_client(monkeypatch, tmp_path)
    created = client.post("/api/decode/sessions", json={"duplex": True, "print_job_id": ""})
    assert created.status_code == 200
    job_id = created.json()["job_id"]
    path = tmp_path / "data" / "scan" / "jobs" / job_id / "job.json"
    meta = json.loads(path.read_text())
    meta["wizard"]["total_pages"] = 4
    meta["wizard"]["data_pages"] = 3
    path.write_text(json.dumps(meta))
    shown = client.get(f"/api/decode/sessions/{job_id}").json()
    assert shown["next_prompt"] == "Put any page face down on the glass. You can start with any sheet."
    assert shown["step"]["action"] == "wait"
    assert shown["readiness"]["state"] == "missing"
    assert shown["readiness"]["parity_pages"] == 1


def test_task_stream_replays_done(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    client = web_client(monkeypatch, tmp_path)
    write_print_job(tmp_path)
    allow_printer(monkeypatch, "ipp://printer.test/ipp/print")
    monkeypatch.setattr("workflows.print_submit.print_pages", lambda *_args, **_kwargs: [4])
    started = client.post("/api/print/jobs/job1", json={"printer": "ipp://printer.test/ipp/print", "confirm": True})
    task_id = started.json()["task_id"]
    wait_task(client, task_id)
    with client.stream("GET", f"/api/tasks/{task_id}/events") as response:
        text = "".join(response.iter_text())
    assert "event: done" in text
