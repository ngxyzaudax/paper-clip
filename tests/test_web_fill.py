import json
from pathlib import Path

import pytest

from web_helpers import small_picks, upload, wait_task, web_client, write_print_job


def test_options_describe_levels_and_the_fill_switch(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    fields = {field["key"]: field for field in web_client(monkeypatch, tmp_path).get("/api/encode/options").json()["fields"]}
    assert fields["paper_size"]["level"] == "simple"
    assert fields["fill_sheets"]["kind"] == "switch"
    assert fields["cell_size_px"]["level"] == "expert"
    assert {option["value"] for option in fields["sides"]["options"]} == {1, 2}


def test_duplex_fill_plans_a_parity_back_and_records_the_sides(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    client = web_client(monkeypatch, tmp_path)
    file_id = upload(client, "note.txt", b"hello paper")
    picks = {**small_picks(), "sides": 2, "fill_sheets": True}
    preview = client.post("/api/encode/preview", json={"file_id": file_id, "picks": picks, "page": 9}).json()
    assert (preview["plan"]["total_pages"], preview["plan"]["parity_pages"], preview["plan"]["sheets"]) == (2, 1, 1)
    assert preview["page"] == 1
    started = client.post("/api/encode", json={"file_id": file_id, "preview_id": preview["preview_id"], "picks": picks})
    job_id = wait_task(client, started.json()["task_id"])["result"]["job_id"]
    meta = json.loads((tmp_path / "data" / "print" / "jobs" / job_id / "job.json").read_text())
    assert (meta["sides"], meta["total_pages"]) == (2, 2)
    assert client.get(f"/api/print/jobs/{job_id}").json()["duplex"] is True


def test_fill_off_keeps_the_single_page(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    client = web_client(monkeypatch, tmp_path)
    file_id = upload(client, "note.txt", b"hello paper")
    picks = {**small_picks(), "sides": 2, "fill_sheets": False}
    plan = client.post("/api/encode/preview", json={"file_id": file_id, "picks": picks}).json()["plan"]
    assert (plan["total_pages"], plan["parity_pages"]) == (1, 0)


def test_single_sided_job_prints_single_sided_by_default(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    client = web_client(monkeypatch, tmp_path)
    write_print_job(tmp_path, "single", sides=1)
    assert client.get("/api/print/jobs/single").json()["duplex"] is False
