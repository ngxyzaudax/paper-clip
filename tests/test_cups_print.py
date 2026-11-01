from pathlib import Path

import pytest

from common.cups_job import _job_number
from common.cups_print import unreachable
from common.cups_queues import CupsQueue, local_queues, queue_name
from common.device_error import DeviceError
from common.ipp_print import print_pages


def test_queue_listing_reads_lpstat() -> None:
    sample = "device for EPSON_ET_8500_Series: dnssd://EPSON%20ET-8500%20Series._ipps._tcp.local./\n"
    assert _parsed(sample) == [CupsQueue("EPSON_ET_8500_Series", "dnssd://EPSON%20ET-8500%20Series._ipps._tcp.local./")]


def test_local_queue_uri_names_the_printer() -> None:
    assert queue_name("ipp://localhost:631/printers/EPSON_ET_8500_Series") == "EPSON_ET_8500_Series"
    assert queue_name("ipp://192.168.1.2:631/ipp/print") is None


def test_job_id_comes_from_the_lp_reply() -> None:
    text = "request id is EPSON_ET_8500_Series-12 (1 file(s))\n"
    assert _job_number(text, "EPSON_ET_8500_Series") == 12


def test_only_a_failed_connection_counts_as_unreachable() -> None:
    assert unreachable(DeviceError("IPP request to 192.168.1.2 failed: [Errno 65] No route to host"))
    assert not unreachable(DeviceError("client-error-document-format-error"))


def test_a_local_queue_is_printed_as_a_pdf(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    sent: list[tuple[str, bool]] = []
    monkeypatch.setattr(
        "common.ipp_print.print_through_queue",
        lambda uri, pages, title, duplex: sent.append((uri, duplex)) or 4,
    )
    monkeypatch.setattr("common.ipp_print.printer_attributes", lambda uri: (_ for _ in ()).throw(AssertionError(uri)))
    page = tmp_path / "page.png"
    page.write_bytes(b"png")
    uri = "ipp://localhost:631/printers/EPSON_ET_8500_Series"
    assert print_pages(uri, [page, page], "paper-clip calibration", duplex=True) == [4]
    assert sent == [(uri, True)]


def test_an_unreachable_printer_uses_the_only_queue(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    sent: list[str] = []

    def offline(uri: str) -> dict[str, list[str]]:
        raise DeviceError("IPP request to 192.168.1.2 failed: [Errno 65] No route to host")

    monkeypatch.setattr("common.ipp_print.printer_attributes", offline)
    monkeypatch.setattr(
        "common.cups_print.only_queue",
        lambda: CupsQueue("EPSON_ET_8500_Series", "dnssd://epson"),
    )
    monkeypatch.setattr(
        "common.ipp_print.print_through_queue",
        lambda uri, pages, title, duplex: sent.append(uri) or 9,
    )
    page = tmp_path / "page.png"
    page.write_bytes(b"png")
    assert print_pages("ipp://192.168.1.2:631/ipp/print", [page], "paper-clip") == [9]
    assert sent == ["ipp://localhost:631/printers/EPSON_ET_8500_Series"]


def _parsed(sample: str) -> list[CupsQueue]:
    import common.cups_queues as cups_queues

    cups_queues.subprocess.run = lambda *args, **kwargs: type("Result", (), {"returncode": 0, "stdout": sample})()
    try:
        return list(local_queues())
    finally:
        cups_queues.subprocess.run = __import__("subprocess").run
