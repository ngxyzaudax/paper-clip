from pathlib import Path

import pytest

from common.ipp_codec import IppMap, unpack_message
from common.ipp_options import PrintTicket
from common.ipp_ticket import job_request

PRINTER_URI = "ipp://printer.example/ipp/print"


def install_fake_printer(
    monkeypatch: pytest.MonkeyPatch,
    attributes: IppMap,
    order: list[str] | None = None,
) -> list[tuple[PrintTicket, bytes, str]]:
    """Replace the IPP calls used by the calibration print path and record what would be sent."""
    submitted: list[tuple[PrintTicket, bytes, str]] = []
    trail = order if order is not None else []

    def submit(uri: str, ticket: PrintTicket, document: bytes, title: str) -> int:
        trail.append("submit")
        submitted.append((ticket, document, title))
        return len(submitted)

    def wait(uri: str, job_id: int) -> str:
        trail.append("wait")
        return "completed"

    monkeypatch.setattr("calibration.print_sheet.printer_attributes", lambda uri: attributes)
    monkeypatch.setattr("calibration.print_sheet.validate_ticket", lambda uri, ticket: trail.append("validate"))
    monkeypatch.setattr("calibration.print_sheet.submit_document", submit)
    monkeypatch.setattr("calibration.print_sheet.wait_for_job", wait)
    monkeypatch.setattr("common.page_document.render_document", _fake_render)
    return submitted


def wire_sides(ticket: PrintTicket) -> list[object]:
    message = unpack_message(job_request(0x0002, PRINTER_URI, "sheet", ticket))
    return list(message.attributes["sides"])


def printer_attributes(sides: list[str], formats: list[str] | None = None) -> IppMap:
    return {
        "document-format-supported": formats or ["image/pwg-raster", "image/jpeg"],
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
        "sides-supported": sides,
        "job-creation-attributes-supported": ["media-col", "print-color-mode", "print-scaling", "sides"],
    }


def _fake_render(page: Path, ticket: PrintTicket) -> bytes:
    return f"{page.name}:{ticket.sides};".encode()
