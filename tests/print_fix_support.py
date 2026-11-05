import json
from collections.abc import Callable
from pathlib import Path

from PIL import Image
from starlette.testclient import TestClient

from common.device_error import DeviceError
from common.types import PrinterInfo, ScannerInfo
from web_helpers import allow_printer, wait_task, web_client, write_print_job

PRINTER = "ipp://printer.test/ipp/print"
SCANNER = "epson2:test"


def prepare(monkeypatch: object, root: Path, job_id: str, sides: int = 1, count: int = 1) -> tuple[TestClient, dict[str, object]]:
    client = web_client(monkeypatch, root)
    pages(root, job_id, count, sides=sides)
    allow_printer(monkeypatch, PRINTER)
    seen: dict[str, object] = {}
    monkeypatch.setattr("workflows.print_submit.print_pages", fake_print(seen))
    return client, seen


def send_print(client: TestClient, payload: dict[str, object], job_id: str) -> dict[str, object]:
    started = client.post(f"/api/print/jobs/{job_id}", json=payload)
    assert started.status_code == 200, started.text
    return wait_task(client, str(started.json()["task_id"]))


def pages(root: Path, job_id: str, count: int, sides: int = 1, paper: str = "A4") -> Path:
    folder = write_print_job(root, job_id, sides)
    meta_path = folder / "job.json"
    meta = json.loads(meta_path.read_text())
    meta["paper_size"] = paper
    meta["sides"] = sides
    meta_path.write_text(json.dumps(meta))
    digital = folder / "digital"
    for path in list(digital.iterdir()):
        path.unlink()
    for index in range(1, count + 1):
        Image.new("RGB", (8, 8), "white").save(digital / f"page_{index:03d}.png")
    return folder


def fake_print(seen: dict[str, object]) -> Callable[..., list[int]]:
    def fake(uri: str, page_paths: list[Path], title: str, paper: str = "A4", duplex: bool = False) -> list[int]:
        seen.update(uri=uri, pages=list(page_paths), paper=paper, duplex=duplex, title=title)
        return [4]
    return fake


def block_print(monkeypatch: object) -> dict[str, bool]:
    called = {"hit": False}

    def fake(*_args: object, **_kwargs: object) -> list[int]:
        called["hit"] = True
        return [1]

    monkeypatch.setattr("workflows.print_submit.print_pages", fake)
    return called


def recorded_duplex(root: Path, job_id: str) -> bool:
    meta = json.loads((root / "data" / "print" / "jobs" / job_id / "job.json").read_text())
    return bool(meta["prints"][0]["duplex"])


def install_hardware(monkeypatch: object, saved: list[tuple[PrinterInfo | None, ScannerInfo | None]]) -> None:
    printers = [PrinterInfo("Press", PRINTER, "idle", True)]
    scanners = [ScannerInfo(SCANNER, "Epson", "ET", "sane")]
    monkeypatch.setattr("web.routes.care_routes.discover_printers", lambda: (printers, PRINTER))
    monkeypatch.setattr("web.routes.care_routes.discover_scanners", lambda: (scanners, SCANNER))
    monkeypatch.setattr("web.routes.care_routes.save_defaults", remember(saved))


def remember(saved: list[tuple[PrinterInfo | None, ScannerInfo | None]]) -> Callable[[PrinterInfo | None, ScannerInfo | None, int], None]:
    def save(printer: PrinterInfo | None, scanner: ScannerInfo | None, _dpi: int) -> None:
        saved.append((printer, scanner))
    return save


def parent_trap(root: Path) -> None:
    digital = root / "data" / "print" / "digital"
    digital.mkdir(parents=True)
    Image.new("RGB", (8, 8), "white").save(digital / "page.png")
    meta = {"source_file": "secret", "created": "2026-01-01T00:00:00", "paper_size": "A4", "data_pages": 1, "sides": 1}
    (digital.parent / "job.json").write_text(json.dumps(meta))


def forbid_discover() -> list[object]:
    raise AssertionError("discover_print_jobs")


def offline(_uri: str, _timeout: float = 20) -> dict[str, object]:
    raise DeviceError("offline")


def offline_caps(_uri: str) -> dict[str, object]:
    raise DeviceError("HTTP 503")
