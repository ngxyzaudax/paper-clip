from pathlib import Path

import pytest

from common.ipp_codec import IppMap
from common.ipp_media import MEDIA_SIZES
from common.ipp_options import build_ticket
from common.ipp_print import print_pages
from common.ipp_ticket import job_request


def test_media_table_uses_integer_a4_points() -> None:
    media = MEDIA_SIZES["A4"]
    assert media.keyword == "iso_a4_210x297mm"
    assert media.points[0] * 360 // 72 == 2975
    assert media.points[1] * 360 // 72 == 4210
    assert MEDIA_SIZES["Letter"].keyword == "na_letter_8.5x11in"


def test_print_pages_validates_before_each_submit(monkeypatch, tmp_path: Path) -> None:
    page = tmp_path / "page.png"
    page.write_bytes(b"png")
    order: list[str] = []

    monkeypatch.setattr("common.ipp_print.printer_attributes", lambda uri: _attributes())
    monkeypatch.setattr("common.ipp_print.validate_ticket", lambda uri, ticket: order.append("validate"))
    monkeypatch.setattr(
        "common.ipp_print.submit_document",
        lambda uri, ticket, document, title: order.append(title) or 8,
    )
    monkeypatch.setattr("common.ipp_print.wait_for_job", lambda uri, job_id: order.append(f"wait-{job_id}"))
    monkeypatch.setattr("common.ipp_print.render_document", lambda page, ticket: b"raster")
    assert print_pages("ipp://printer.example/ipp/print", [page, page], "paper-clip") == [8, 8]
    assert order == ["validate", "paper-clip (1/2)", "wait-8", "paper-clip (2/2)", "wait-8"]


def test_print_pages_rejects_an_empty_list() -> None:
    with pytest.raises(ValueError, match="no pages"):
        print_pages("ipp://printer.example/ipp/print", [], "paper-clip")


def test_jpeg_ticket_keeps_resolution_and_pwg_omits_it() -> None:
    jpeg = _attributes()
    jpeg["document-format-supported"] = ["image/jpeg", "application/vnd.epson.escpr"]
    ticket = build_ticket(jpeg, "A4")
    raw = job_request(0x0002, "ipp://printer.example/ipp/print", "page", ticket, b"jpeg")
    assert ticket.document_format == "image/jpeg"
    assert raw.endswith(b"jpeg")
    assert b"printer-resolution" in raw
    pwg_raw = job_request(0x0002, "ipp://printer.example/ipp/print", "page", build_ticket(_attributes(), "A4"))
    assert b"printer-resolution" not in pwg_raw


def _attributes() -> IppMap:
    return {
        "document-format-supported": ["image/pwg-raster", "image/jpeg"],
        "pwg-raster-document-resolution-supported": [(360, 360, 3)],
        "media-supported": ["iso_a4_210x297mm"],
        "media-source-supported": ["main"],
        "media-top-margin-supported": [300],
        "media-bottom-margin-supported": [300],
        "media-left-margin-supported": [300],
        "media-right-margin-supported": [300],
        "print-color-mode-supported": ["color"],
        "print-quality-supported": [5],
        "print-scaling-supported": ["none"],
        "sides-supported": ["one-sided"],
        "job-creation-attributes-supported": [
            "media-col", "print-color-mode", "print-scaling", "sides",
        ],
    }
