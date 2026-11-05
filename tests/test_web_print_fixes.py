import json
from pathlib import Path

import pytest

from common.device_error import DeviceError
from print_fix_support import (
    PRINTER,
    SCANNER,
    block_print,
    forbid_discover,
    install_hardware,
    offline,
    offline_caps,
    pages,
    parent_trap,
    prepare,
    recorded_duplex,
    send_print,
)
from web_helpers import allow_printer, web_client, write_print_job
from workflows.print_jobs import job_by_id
from workflows.scan_discovery import resolve_max_dpi


def test_omitted_duplex_follows_job_sides(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    client, seen = prepare(monkeypatch, tmp_path, "both", sides=2)
    finished = send_print(client, {"printer": PRINTER, "confirm": True}, "both")
    assert finished["state"] == "done", finished
    assert seen["duplex"] is True
    assert recorded_duplex(tmp_path, "both") is True


def test_explicit_duplex_false_wins(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    client, seen = prepare(monkeypatch, tmp_path, "single", sides=2)
    finished = send_print(client, {"printer": PRINTER, "duplex": False, "confirm": True}, "single")
    assert finished["state"] == "done", finished
    assert seen["duplex"] is False
    assert recorded_duplex(tmp_path, "single") is False


def test_unknown_printer_is_rejected(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    client = web_client(monkeypatch, tmp_path)
    write_print_job(tmp_path)
    allow_printer(monkeypatch, PRINTER)
    called = block_print(monkeypatch)
    response = client.post("/api/print/jobs/job1", json={"printer": "ipp://other.example/ipp/print", "confirm": True})
    assert response.status_code == 400
    assert "ipp://other.example/ipp/print" in response.text
    assert called["hit"] is False


def test_unknown_paper_size_is_rejected(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    client = web_client(monkeypatch, tmp_path)
    pages(tmp_path, "job1", 1, paper="Tabloid")
    allow_printer(monkeypatch, PRINTER)
    called = block_print(monkeypatch)
    response = client.post("/api/print/jobs/job1", json={"printer": PRINTER, "confirm": True})
    assert response.status_code == 400
    assert "Tabloid" in response.text
    assert called["hit"] is False


def test_single_sided_message_counts_pages(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    client, _seen = prepare(monkeypatch, tmp_path, "job1", count=2)
    finished = send_print(client, {"printer": PRINTER, "duplex": False, "confirm": True}, "job1")
    assert finished["state"] == "done", finished
    assert finished["result"]["message"] == f"Submitted 2 page(s) to {PRINTER}. Job IDs: 4"


def test_unknown_device_is_not_saved(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    client = web_client(monkeypatch, tmp_path)
    saved: list[tuple[object, object]] = []
    install_hardware(monkeypatch, saved)
    missing_printer = client.post("/api/devices", json={"printer_uri": "ipp://missing", "scanner_id": SCANNER})
    assert missing_printer.status_code == 400
    assert "ipp://missing" in missing_printer.text
    missing_scanner = client.post("/api/devices", json={"printer_uri": PRINTER, "scanner_id": "no-such-scanner"})
    assert missing_scanner.status_code == 400
    assert "no-such-scanner" in missing_scanner.text
    assert saved == []
    saved_ok = client.post("/api/devices", json={"printer_uri": PRINTER, "scanner_id": SCANNER})
    assert saved_ok.status_code == 200
    assert saved_ok.json()["message"] == "Saved defaults"
    assert saved[0][0] is not None and saved[0][0].uri == PRINTER
    assert saved[0][1] is not None and saved[0][1].device_id == SCANNER


def test_broken_job_metadata_is_skipped(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    client = web_client(monkeypatch, tmp_path)
    write_print_job(tmp_path, "good")
    (write_print_job(tmp_path, "bad") / "job.json").write_text("{")
    ugly = write_print_job(tmp_path, "ugly")
    meta = json.loads((ugly / "job.json").read_text())
    meta["data_pages"] = "nope"
    (ugly / "job.json").write_text(json.dumps(meta))
    listed = client.get("/api/print/jobs")
    assert listed.status_code == 200
    assert [item["job_id"] for item in listed.json()] == ["good"]


def test_job_by_id_rejects_parent_segment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    web_client(monkeypatch, tmp_path)
    write_print_job(tmp_path, "job1")
    parent_trap(tmp_path)
    monkeypatch.setattr("workflows.print_jobs.discover_print_jobs", forbid_discover)
    assert job_by_id("..") is None
    assert job_by_id("job1/../job1") is None
    found = job_by_id("job1")
    assert found is not None
    assert found.job_id == "job1"


def test_devices_without_hardware_stay_empty(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    client = web_client(monkeypatch, tmp_path)
    monkeypatch.setattr("web.routes.care_routes.discover_printers", lambda: ([], None))
    monkeypatch.setattr("web.routes.care_routes.discover_scanners", lambda: ([], None))
    response = client.get("/api/devices")
    body = response.json()
    assert response.status_code == 200
    assert body["printers"] == []
    assert body["scanners"] == []
    assert body["printer_caps"] == {}
    assert body["scanner_caps"] == {}


def test_capability_failures_are_rejected(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    client = web_client(monkeypatch, tmp_path)
    monkeypatch.setattr("common.ipp_client.printer_attributes", offline)
    printer = client.get("/api/devices/printer", params={"uri": PRINTER})
    assert printer.status_code == 400
    assert "offline" in printer.text
    monkeypatch.setattr("common.sane_discovery.get_scanner_capabilities", lambda _device: None)
    scanner = client.get("/api/devices/scanner", params={"device": SCANNER})
    assert scanner.status_code == 400
    assert "Could not read capabilities" in scanner.text


def test_failed_escl_read_raises_and_sane_can_be_unknown(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("workflows.scan_discovery.read_escl_caps", offline_caps)
    with pytest.raises(DeviceError, match="scanner did not answer"):
        resolve_max_dpi("https://scanner.test/eSCL")
    monkeypatch.setattr("workflows.scan_discovery.get_scanner_capabilities", lambda _device: None)
    assert resolve_max_dpi("epson2:test") is None
