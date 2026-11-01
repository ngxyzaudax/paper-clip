from pathlib import Path

import pytest

from common.device_error import DeviceError
from common.ipp_codec import IppMap, unpack_message
from common.ipp_options import PrintTicket
from common.ipp_print import print_pages
from common.ipp_ticket import job_request

_URI = "ipp://printer.example/ipp/print"


@pytest.mark.parametrize(
    ("supported", "sides"),
    [
        (["one-sided", "two-sided-long-edge", "two-sided-short-edge"], "two-sided-long-edge"),
        (["two-sided-long-edge"], "two-sided-long-edge"),
        (["two-sided-short-edge"], "two-sided-short-edge"),
    ],
)
def test_duplex_option_builds_one_two_sided_job(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    supported: list[str],
    sides: str,
) -> None:
    pages = [tmp_path / name for name in ("page_001.png", "page_002.png", "page_003.png")]
    submitted = _install(monkeypatch, _attributes(supported))
    assert print_pages(_URI, pages, "paper-clip", duplex=True) == [1]
    ticket, document, title = submitted[0]
    assert (len(submitted), title, ticket.sides) == (1, "paper-clip", sides)
    assert document == "".join(f"{page.name}:{sides};" for page in pages).encode()
    assert _wire_sides(ticket) == [sides]


def test_omitted_duplex_option_stays_one_sided(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    pages = [tmp_path / "page_001.png", tmp_path / "page_002.png"]
    submitted = _install(monkeypatch, _attributes(["one-sided", "two-sided-long-edge"]))
    assert print_pages(_URI, pages, "paper-clip") == [1, 2]
    assert [ticket.sides for ticket, _document, _title in submitted] == ["one-sided", "one-sided"]
    assert [document for _ticket, document, _title in submitted] == [
        b"page_001.png:one-sided;",
        b"page_002.png:one-sided;",
    ]


@pytest.mark.parametrize("supported", [["one-sided"], []])
def test_duplex_option_errors_when_duplex_is_not_advertised(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    supported: list[str],
) -> None:
    submitted = _install(monkeypatch, _attributes(supported))
    with pytest.raises(DeviceError, match="does not advertise duplex"):
        print_pages(_URI, [tmp_path / "page.png"], "paper-clip", duplex=True)
    assert submitted == []


def test_print_cli_duplex_flag_keeps_page_order(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    pages = [tmp_path / "page_001.png", tmp_path / "page_002.png"]
    for page in pages:
        page.write_bytes(b"png")
    seen: dict[str, object] = {}

    def fake_print(
        uri: str,
        got: list[Path],
        title: str,
        paper: str = "A4",
        duplex: bool = False,
    ) -> list[int]:
        seen.update(uri=uri, pages=got, paper=paper, duplex=duplex)
        return [9]

    monkeypatch.setattr("cli.print_cmd.print_pages", fake_print)
    from typer.testing import CliRunner
    from cli.app import app

    result = CliRunner().invoke(
        app,
        ["print", str(pages[0]), str(pages[1]), "--duplex", "--uri", _URI, "--paper", "A4"],
    )
    assert result.exit_code == 0, result.output
    assert seen == {"uri": _URI, "pages": pages, "paper": "A4", "duplex": True}
    plain = CliRunner().invoke(app, ["print", str(pages[0]), "--uri", _URI, "--paper", "A4"])
    assert plain.exit_code == 0, plain.output
    assert seen["duplex"] is False
    assert seen["pages"] == [pages[0]]


def test_duplex_option_errors_when_both_sides_cannot_share_a_document(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    submitted = _install(
        monkeypatch,
        _attributes(["one-sided", "two-sided-long-edge"], ["image/jpeg"]),
    )
    with pytest.raises(DeviceError, match="one PWG document"):
        print_pages(_URI, [tmp_path / "a.png", tmp_path / "b.png"], "paper-clip", duplex=True)
    assert submitted == []


def _install(
    monkeypatch: pytest.MonkeyPatch,
    attributes: IppMap,
) -> list[tuple[PrintTicket, bytes, str]]:
    submitted: list[tuple[PrintTicket, bytes, str]] = []

    def submit(uri: str, ticket: PrintTicket, document: bytes, title: str) -> int:
        submitted.append((ticket, document, title))
        return len(submitted)

    def render(page: Path, ticket: PrintTicket) -> bytes:
        return f"{page.name}:{ticket.sides};".encode()

    monkeypatch.setattr("common.ipp_print.printer_attributes", lambda uri: attributes)
    monkeypatch.setattr("common.ipp_print.validate_ticket", lambda uri, ticket: None)
    monkeypatch.setattr("common.ipp_print.submit_document", submit)
    monkeypatch.setattr("common.ipp_print.wait_for_job", lambda uri, job_id: "completed")
    monkeypatch.setattr("common.page_document.render_document", render)
    monkeypatch.setattr("common.ipp_print.render_document", render)
    return submitted


def _wire_sides(ticket: PrintTicket) -> list[object]:
    message = unpack_message(job_request(0x0002, _URI, "paper-clip", ticket))
    return list(message.attributes["sides"])


def _attributes(sides: list[str], formats: list[str] | None = None) -> IppMap:
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
        "job-creation-attributes-supported": [
            "media-col", "print-color-mode", "print-scaling", "sides",
        ],
    }
