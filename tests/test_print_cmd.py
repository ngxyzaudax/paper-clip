from pathlib import Path

import pytest
import typer

from cli.print_cmd import _saved_or_only_printer, print_command
from common.types import PrinterInfo


def test_print_command_uses_the_given_uri_and_paper(monkeypatch, tmp_path: Path) -> None:
    page = tmp_path / "page.png"
    page.write_bytes(b"png")
    seen: dict[str, object] = {}

    def fake_print(uri: str, pages: list[Path], title: str, paper: str = "A4") -> list[int]:
        seen["uri"] = uri
        seen["paper"] = paper
        seen["pages"] = pages
        return [11]

    monkeypatch.setattr("cli.print_cmd.print_pages", fake_print)
    print_command(page, "ipps://printer.example:631/ipp/print", "A5")
    assert seen["uri"] == "ipps://printer.example:631/ipp/print"
    assert seen["paper"] == "A5"
    assert seen["pages"] == [page]


def test_print_command_uses_the_saved_printer(monkeypatch, tmp_path: Path) -> None:
    page = tmp_path / "page.png"
    page.write_bytes(b"png")
    monkeypatch.setattr(
        "cli.print_cmd.get_printer_settings",
        lambda: {"uri": "ipp://saved.example:631/ipp/print", "paper_size": "Letter"},
    )
    seen: dict[str, str] = {}
    monkeypatch.setattr(
        "cli.print_cmd.print_pages",
        lambda uri, pages, title, paper="A4": seen.update(uri=uri, paper=paper) or [2],
    )
    print_command(page, None, None)
    assert seen == {"uri": "ipp://saved.example:631/ipp/print", "paper": "Letter"}


def test_print_command_rejects_a_missing_page_and_unknown_paper(tmp_path: Path) -> None:
    with pytest.raises(typer.Exit):
        print_command(tmp_path / "missing.png", "ipp://printer.example/ipp/print", "A4")
    page = tmp_path / "page.png"
    page.write_bytes(b"png")
    with pytest.raises(typer.Exit):
        print_command(page, "ipp://printer.example/ipp/print", "Tabloid")


def test_saved_or_only_printer_requires_one_match(monkeypatch) -> None:
    monkeypatch.setattr("cli.print_cmd.get_printer_settings", lambda: {"uri": ""})
    monkeypatch.setattr("cli.print_cmd.list_ipp_printers", lambda: [])
    with pytest.raises(Exception, match="no IPP printer"):
        _saved_or_only_printer()
    monkeypatch.setattr(
        "cli.print_cmd.list_ipp_printers",
        lambda: [
            PrinterInfo("a", "ipp://a/ipp/print", "driverless", False),
            PrinterInfo("b", "ipp://b/ipp/print", "driverless", False),
        ],
    )
    with pytest.raises(Exception, match="multiple IPP"):
        _saved_or_only_printer()
