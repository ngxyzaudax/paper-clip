import pytest

from common.device_error import DeviceError
from common.ipp_codec import unpack_message
from common.ipp_options import build_ticket
from common.ipp_ticket import job_request


def _printer(**overrides: object) -> dict[str, list[object]]:
    attributes: dict[str, list[object]] = {
        "document-format-supported": ["image/pwg-raster", "image/jpeg", "application/vnd.epson.escpr"],
        "pwg-raster-document-resolution-supported": [(360, 360, 3)],
        "media-supported": ["iso_a4_210x297mm", "na_letter_8.5x11in"],
        "media-source-supported": ["auto", "main", "rear", "photo"],
        "media-top-margin-supported": [0, 300],
        "media-bottom-margin-supported": [0, 300],
        "media-left-margin-supported": [0, 300],
        "media-right-margin-supported": [0, 300],
        "print-color-mode-supported": ["color", "monochrome"],
        "print-quality-supported": [4, 5],
        "print-scaling-supported": ["auto", "fit", "none"],
        "sides-supported": ["one-sided", "two-sided-long-edge"],
        "job-creation-attributes-supported": [
            "media", "media-col", "print-color-mode", "print-quality",
            "print-scaling", "sides", "printer-resolution",
        ],
    }
    attributes.update(overrides)
    return attributes


def test_ticket_is_bordered_color_and_unscaled() -> None:
    ticket = build_ticket(_printer(), "A4")
    assert ticket.media.keyword == "iso_a4_210x297mm"
    assert ticket.source == "main"
    assert ticket.margin == 300
    assert ticket.color == "color"
    assert ticket.quality == 5
    assert ticket.scaling == "none"
    assert ticket.sides == "one-sided"
    assert ticket.dpi == 360
    assert ticket.document_format == "image/pwg-raster"
    assert "escpr" not in ticket.document_format


def test_ticket_refuses_borderless_only_margins() -> None:
    with pytest.raises(DeviceError, match="bordered"):
        build_ticket(_printer(**{
            "media-top-margin-supported": [0],
            "media-bottom-margin-supported": [0],
            "media-left-margin-supported": [0],
            "media-right-margin-supported": [0],
        }), "A4")


def test_ticket_refuses_fit_to_page_only() -> None:
    with pytest.raises(DeviceError, match="100%"):
        build_ticket(_printer(**{"print-scaling-supported": ["fit", "auto"]}), "A4")


def test_ticket_refuses_a_printer_that_cannot_accept_media_col() -> None:
    with pytest.raises(DeviceError, match="media-col"):
        build_ticket(_printer(**{"job-creation-attributes-supported": ["media"]}), "A4")


def test_ticket_refuses_rear_only_feed() -> None:
    with pytest.raises(DeviceError, match="cassette"):
        build_ticket(_printer(**{"media-source-supported": ["rear", "photo"]}), "A4")


def test_job_request_carries_positive_margins_and_no_scaling() -> None:
    ticket = build_ticket(_printer(), "A4")
    message = unpack_message(job_request(0x0004, "ipp://printer.local:631/ipp/print", "page", ticket))
    assert message.attributes["print-scaling"] == ["none"]
    assert message.attributes["print-color-mode"] == ["color"]
    assert message.attributes["sides"] == ["one-sided"]
    assert message.attributes["print-quality"] == [5]
    assert message.attributes["media"] == ["iso_a4_210x297mm"]
    media_col = message.attributes["media-col"][0]
    assert isinstance(media_col, dict)
    assert media_col["media-source"] == ["main"]
    assert media_col["media-top-margin"] == [300]
    assert media_col["media-bottom-margin"] == [300]
    assert 0 not in media_col["media-top-margin"]
    size = media_col["media-size"][0]
    assert isinstance(size, dict)
    assert size["x-dimension"] == [21000]
    assert size["y-dimension"] == [29700]
    assert message.attributes["document-format"] == ["image/pwg-raster"]
    assert message.attributes["ipp-attribute-fidelity"] == [True]
    assert b"\x4a\x00\x00\x00\x0bx-dimension" in job_request(
        0x0004, "ipp://printer.local:631/ipp/print", "page", ticket,
    )
