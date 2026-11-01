from pathlib import Path

import pytest

from calibration.print_sheet import print_calibration_sheet
from common.device_error import DeviceError
from common.ipp_options import PrintTicket, build_ticket
from common.page_document import render_pages
from fake_ipp_printer import PRINTER_URI as _URI
from fake_ipp_printer import install_fake_printer as _install
from fake_ipp_printer import printer_attributes as _attributes
from fake_ipp_printer import wire_sides as _wire_sides

_NO_DUPLEX = "This printer does not advertise duplex. Two sheets will be used."
_NO_DOCUMENT = "This printer cannot put both sides in one document. Two sheets will be used."


@pytest.mark.parametrize(
    ("supported", "sides"),
    [
        (["one-sided", "two-sided-long-edge", "two-sided-short-edge"], "two-sided-long-edge"),
        (["two-sided-long-edge"], "two-sided-long-edge"),
        (["two-sided-short-edge"], "two-sided-short-edge"),
    ],
)
def test_calibration_is_one_duplex_document_when_available(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    supported: list[str],
    sides: str,
) -> None:
    order: list[str] = []
    submitted = _install(monkeypatch, _attributes(supported), order)
    job = print_calibration_sheet(_URI, tmp_path / "front.png", tmp_path / "back.png", _forbid)
    ticket, document, title = submitted[0]
    assert (job.sheets, job.sides, job.job_ids) == (1, sides, [1])
    assert order == ["validate", "submit", "wait"]
    assert len(submitted) == 1
    assert title == "paper-clip calibration"
    assert document == f"front.png:{sides};back.png:{sides};".encode()
    assert _wire_sides(ticket) == [sides]


@pytest.mark.parametrize("supported", [["one-sided"], []])
def test_calibration_uses_two_one_sided_sheets_without_duplex(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    supported: list[str],
) -> None:
    order: list[str] = []
    submitted = _install(monkeypatch, _attributes(supported), order)
    job = print_calibration_sheet(_URI, tmp_path / "front.png", tmp_path / "back.png", order.append)
    assert (job.sheets, job.sides, job.job_ids) == (2, "one-sided", [1, 2])
    assert order[0] == _NO_DUPLEX
    assert order[1:] == ["validate", "submit", "wait", "validate", "submit", "wait"]
    assert [title for _ticket, _document, title in submitted] == [
        "paper-clip calibration front",
        "paper-clip calibration back",
    ]
    assert [document for _ticket, document, _title in submitted] == [
        b"front.png:one-sided;",
        b"back.png:one-sided;",
    ]
    assert [_wire_sides(ticket) for ticket, _document, _title in submitted] == [["one-sided"], ["one-sided"]]


def test_jpeg_duplex_printer_still_uses_two_one_sided_sheets(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    order: list[str] = []
    submitted = _install(
        monkeypatch,
        _attributes(["one-sided", "two-sided-long-edge"], ["image/jpeg"]),
        order,
    )
    job = print_calibration_sheet(_URI, tmp_path / "front.png", tmp_path / "back.png", order.append)
    assert (job.sheets, job.sides) == (2, "one-sided")
    assert len(submitted) == 2
    assert order[0] == _NO_DOCUMENT
    assert [_wire_sides(ticket) for ticket, _document, _title in submitted] == [["one-sided"], ["one-sided"]]


def test_a_rejected_calibration_job_is_submitted_once(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    trail: list[str] = []

    def submit(uri: str, ticket: PrintTicket, document: bytes, title: str) -> int:
        trail.append("submit")
        raise DeviceError("client-error-document-format-error")

    _install(monkeypatch, _attributes(["two-sided-long-edge"]))
    monkeypatch.setattr("calibration.print_sheet.submit_document", submit)
    with pytest.raises(DeviceError, match="document-format-error"):
        print_calibration_sheet(_URI, tmp_path / "front.png", tmp_path / "back.png", _forbid)
    assert trail == ["submit"]


def test_render_pages_rejects_two_jpeg_sides() -> None:
    ticket = build_ticket(
        _attributes(["one-sided", "two-sided-long-edge"], ["image/jpeg"]),
        "A4",
        "two-sided-long-edge",
    )
    with pytest.raises(DeviceError, match="PWG raster"):
        render_pages([Path("front.png"), Path("back.png")], ticket)


def _forbid(message: str) -> None:
    raise AssertionError(message)
