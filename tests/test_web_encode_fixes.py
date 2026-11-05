import json
from pathlib import Path

import pytest

from web.preview_cache import matching_encode, request_key
from workflows.picks_parse import picks_from_dict
from web_helpers import small_picks, upload, wait_task, web_client


def test_inbox_ids_cannot_leave_the_inbox(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    client = web_client(monkeypatch, tmp_path)
    (tmp_path / "data" / "secret").mkdir(parents=True)
    (tmp_path / "data" / "secret" / "key.txt").write_text("private")
    response = client.post("/api/encode/preview", json={"file_id": "../secret", "picks": small_picks()})
    assert response.status_code in (400, 404)


def test_an_empty_upload_is_refused_and_leaves_no_folder(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    client = web_client(monkeypatch, tmp_path)
    response = client.post("/api/inbox", files={"file": ("empty.bin", b"", "application/octet-stream")})
    assert response.status_code == 400
    assert not any((tmp_path / "data" / "inbox").glob("*/*"))


def test_picks_outside_the_catalog_are_refused(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    client = web_client(monkeypatch, tmp_path)
    for picks in ({"cell_size_px": 3}, {"paper_size": "Napkin"}, {"sides": True}, {"symbol_count": [8]}):
        assert client.post("/api/encode/preview", json={"picks": picks}).status_code in (400, 422), picks


def test_boolean_words_parse_both_ways() -> None:
    assert picks_from_dict({"fill_sheets": "false"}).fill_sheets is False
    assert picks_from_dict({"fill_sheets": "on"}).fill_sheets is True
    with pytest.raises(ValueError):
        picks_from_dict({"fill_sheets": "maybe"})


def test_a_preview_is_reused_only_for_the_same_request(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    client = web_client(monkeypatch, tmp_path)
    file_id = upload(client, "note.txt", b"hello paper")
    preview = client.post("/api/encode/preview", json={"file_id": file_id, "picks": small_picks()}).json()
    picks = picks_from_dict(small_picks())
    assert matching_encode(preview["preview_id"], request_key(file_id, picks, None)) is not None
    assert matching_encode(preview["preview_id"], request_key(file_id, picks, "hunter2")) is None
    assert matching_encode(preview["preview_id"], request_key(file_id, picks_from_dict({**small_picks(), "sides": 2}), None)) is None


def test_encode_applies_a_passphrase_added_after_the_preview(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    client = web_client(monkeypatch, tmp_path)
    file_id = upload(client, "note.txt", b"hello paper")
    preview = client.post("/api/encode/preview", json={"file_id": file_id, "picks": small_picks()}).json()
    body = {"file_id": file_id, "preview_id": preview["preview_id"], "picks": small_picks(), "passphrase": "hunter2"}
    result = wait_task(client, client.post("/api/encode", json=body).json()["task_id"])
    job = tmp_path / "data" / "print" / "jobs" / str(result["result"]["job_id"])
    assert "hunter2" not in (job / "job.json").read_text()
    with_secret = client.post("/api/encode/preview", json={"file_id": file_id, "picks": small_picks(), "passphrase": "hunter2"}).json()
    assert with_secret["plan"]["passphrase_required"] is True
    assert json.loads((job / "job.json").read_text())["payload_bytes"] == with_secret["plan"]["payload_bytes"]


def test_layout_only_preview_reports_every_plan_key(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    plan = web_client(monkeypatch, tmp_path).post("/api/encode/preview", json={"picks": small_picks()}).json()["plan"]
    assert plan["passphrase_required"] is False
    assert set(plan["requested"]) == {"ecc_sym", "cell_size_px", "parity_pages"}
