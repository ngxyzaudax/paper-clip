import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from common.json_file import JsonFileError
from decode_fix_helpers import claim_together, put_scans, session_id
from serialization.decode.errors import DecodeError
from serialization.decode.observation import PageObservation
from web.page_quality import page_quality
from web_helpers import web_client, write_print_job
from workflows.scan_jobs import count_scans, next_scan_path, start_scan_job, update_scan_job_metadata
from workflows.scan_list import discover_scan_jobs
from workflows.wizard_state import load_wizard, save_wizard, session_dir, update_scan


def test_job_ids_cannot_escape_the_scan_root(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    client = web_client(monkeypatch, tmp_path)
    assert client.get("/api/decode/sessions/%2e%2e").status_code in (400, 404)
    assert client.get("/api/decode/sessions/missing-session").status_code == 404
    for value in ("..", "a/b"):
        with pytest.raises(ValueError):
            session_dir(value)


def test_keep_does_not_collapse_unidentified_scans(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    client = web_client(monkeypatch, tmp_path)
    job_id = session_id(client, {"duplex": False})
    folder = tmp_path / "data" / "scan" / "jobs" / job_id
    for name in ("scan_001.png", "scan_002.png", "scan_003.png"):
        Image.new("RGB", (4, 4), "white").save(folder / "scans" / name)
    put_scans(folder / "job.json", [
        {"name": "scan_001.png", "page_index": 0, "status": "identified", "kept": True},
        {"name": "scan_002.png", "page_index": 0, "status": "two-pages", "kept": False, "page_indices": [0, 1]},
        {"name": "scan_003.png", "page_index": None, "status": "unidentified", "kept": True},
    ])
    shown = client.post(f"/api/decode/sessions/{job_id}/scans/scan_002.png/keep")
    assert shown.status_code == 200, shown.text
    rows = {item["name"]: item for item in shown.json()["scans"]}
    assert (rows["scan_002.png"]["kept"], rows["scan_002.png"]["status"]) == (True, "two-pages")
    assert rows["scan_002.png"]["page_indices"] == [0, 1]
    assert (rows["scan_001.png"]["kept"], rows["scan_001.png"]["status"]) == (False, "duplicate")
    assert (rows["scan_003.png"]["kept"], rows["scan_003.png"]["status"]) == (True, "unidentified")


def test_next_scan_path_reserves_exclusively(tmp_path: Path) -> None:
    scans = tmp_path / "scans"
    scans.mkdir()
    (scans / "scan_001.png").write_bytes(b"kept")
    reserved = next_scan_path(tmp_path)
    assert (reserved.name, reserved.stat().st_size) == ("scan_002.png", 0)
    assert (scans / "scan_001.png").read_bytes() == b"kept"
    assert next_scan_path(tmp_path, ".jpg").name == "scan_003.jpg"
    assert len(claim_together(tmp_path, 4)) == 4


def test_non_image_upload_is_removed(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    client = web_client(monkeypatch, tmp_path)
    job_id = session_id(client, {"duplex": False})
    response = client.post(
        f"/api/decode/sessions/{job_id}/upload",
        files={"files": ("notes.txt", b"not an image", "text/plain")},
    )
    assert response.status_code == 400
    assert list((tmp_path / "data" / "scan" / "jobs" / job_id / "scans").iterdir()) == []


def test_setup_keeps_duplex_when_only_the_print_job_is_sent(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    client = web_client(monkeypatch, tmp_path)
    job_id = session_id(client, {"duplex": True, "print_job_id": ""})
    kept = client.post(f"/api/decode/sessions/{job_id}/setup", json={"print_job_id": "later"})
    assert kept.status_code == 200, kept.text
    assert kept.json()["duplex"] is True and kept.json()["print_job_id"] == "later"
    cleared = client.post(f"/api/decode/sessions/{job_id}/setup", json={"duplex": "false"})
    assert cleared.status_code == 200, cleared.text
    assert cleared.json()["duplex"] is False and cleared.json()["print_job_id"] == "later"


def test_unknown_print_job_is_missing_and_omitted_duplex_uses_sides(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    client = web_client(monkeypatch, tmp_path)
    assert client.post("/api/decode/sessions", json={"print_job_id": "missing"}).status_code == 404
    write_print_job(tmp_path, "job1", sides=2)
    created = client.post("/api/decode/sessions", json={"print_job_id": "job1"})
    assert created.status_code == 200, created.text
    assert created.json()["duplex"] is True
    single = client.post("/api/decode/sessions", json={"print_job_id": "job1", "duplex": False})
    assert single.json()["duplex"] is False


def test_empty_sessions_stay_listed_with_sha256(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    client = web_client(monkeypatch, tmp_path)
    job_id = session_id(client, {"duplex": False})
    assert discover_scan_jobs() == []
    listed = client.get("/api/decode/sessions").json()
    assert listed[0]["job_id"] == job_id and listed[0]["pages"] == 0 and listed[0]["sha256"] == ""
    path = tmp_path / "data" / "scan" / "jobs" / job_id / "job.json"
    meta = json.loads(path.read_text())
    meta["wizard"]["sha256"] = "abc123"
    path.write_text(json.dumps(meta))
    assert client.get("/api/decode/sessions").json()[0]["sha256"] == "abc123"


def test_damaged_job_json_is_not_replaced(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    client = web_client(monkeypatch, tmp_path)
    job_id = session_id(client, {"duplex": True})
    path = tmp_path / "data" / "scan" / "jobs" / job_id / "job.json"
    path.write_text("{")
    with pytest.raises(JsonFileError):
        update_scan_job_metadata(path.parent, 600, "Gray")
    with pytest.raises(JsonFileError):
        save_wizard(job_id, {"duplex": False, "scans": []})
    failed = client.post(f"/api/decode/sessions/{job_id}/setup", json={"duplex": False})
    assert failed.status_code >= 400 and path.read_text() == "{"
    assert discover_scan_jobs(include_empty=True) == []

def test_remove_missing_scan_is_not_found(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    client = web_client(monkeypatch, tmp_path)
    assert client.delete("/api/decode/sessions/missing/scans/scan_001.png").status_code == 404
    job_id = session_id(client, {"duplex": False})
    assert client.delete(f"/api/decode/sessions/{job_id}/scans/scan_001.png").status_code == 404
    assert client.delete(f"/api/decode/sessions/{job_id}/scans/%2e%2e").status_code in (400, 404)


def test_count_scans_counts_images(tmp_path: Path) -> None:
    scans = tmp_path / "scans"
    scans.mkdir()
    (scans / "scan_001.png").write_bytes(b"x")
    (scans / "notes.txt").write_bytes(b"x")
    assert count_scans(tmp_path) == 1

def test_update_scan_appends_a_missing_name(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    ctx = start_scan_job("upload", 300)
    save_wizard(ctx.job_id, {"duplex": False, "scans": []})
    update_scan(ctx.job_id, "scan_009.png", {"status": "unidentified", "kept": True, "page_index": None})
    stored = json.loads((ctx.job_dir / "job.json").read_text())["wizard"]["scans"]
    assert stored[0]["status"] == "unidentified"
    Image.new("RGB", (2, 2), "white").save(ctx.job_dir / "scans" / "scan_009.png")
    assert load_wizard(ctx.job_id)["scans"][0]["kept"] is True


def test_unreadable_page_quality_is_unread(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(_image: np.ndarray, _model: object | None = None) -> PageObservation:
        raise DecodeError("page header not found")
    monkeypatch.setattr("web.page_quality.observe_page", fail)
    assert page_quality(np.zeros((2, 2, 3), dtype=np.uint8))["quality"] == "unread"
