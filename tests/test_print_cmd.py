from pathlib import Path

import pytest
import typer

from cli.print_cmd import _saved_or_only_printer, print_command
from cli.tui.print_form import submit_print_job
from cli.tui.print_jobs import PrintJob
from common.types import PrinterInfo


def test_print_command_uses_the_given_uri_and_paper(monkeypatch, tmp_path: Path) -> None:
    page = tmp_path / "page.png"
    page.write_bytes(b"png")
    seen: dict[str, object] = {}

    def fake_print(
        uri: str,
        pages: list[Path],
        title: str,
        paper: str = "A4",
        duplex: bool = False,
    ) -> list[int]:
        seen["uri"] = uri
        seen["paper"] = paper
        seen["pages"] = pages
        seen["duplex"] = duplex
        seen["title"] = title
        return [11]

    monkeypatch.setattr("cli.print_cmd.print_pages", fake_print)
    print_command([page], "ipps://printer.example:631/ipp/print", "A5", False)
    assert seen["uri"] == "ipps://printer.example:631/ipp/print"
    assert seen["paper"] == "A5"
    assert seen["pages"] == [page]
    assert seen["duplex"] is False
    assert seen["title"] == "paper-clip page.png"


def test_print_command_uses_the_saved_printer(monkeypatch, tmp_path: Path) -> None:
    page = tmp_path / "page.png"
    page.write_bytes(b"png")
    monkeypatch.setattr(
        "cli.print_cmd.get_printer_settings",
        lambda: {"uri": "ipp://saved.example:631/ipp/print", "paper_size": "Letter"},
    )
    seen: dict[str, object] = {}
    monkeypatch.setattr(
        "cli.print_cmd.print_pages",
        lambda uri, pages, title, paper="A4", duplex=False: seen.update(uri=uri, paper=paper, duplex=duplex) or [2],
    )
    print_command([page], None, None, False)
    assert seen == {"uri": "ipp://saved.example:631/ipp/print", "paper": "Letter", "duplex": False}


def test_print_command_passes_duplex_and_page_order(monkeypatch, tmp_path: Path) -> None:
    pages = [_page(tmp_path, name) for name in ("page_001.png", "page_002.png", "page_003.png")]
    seen: dict[str, object] = {}

    def fake_print(
        uri: str,
        got: list[Path],
        title: str,
        paper: str = "A4",
        duplex: bool = False,
    ) -> list[int]:
        seen["pages"] = got
        seen["duplex"] = duplex
        seen["title"] = title
        return [7]

    monkeypatch.setattr("cli.print_cmd.print_pages", fake_print)
    print_command(pages, "ipp://printer.example/ipp/print", "A4", True)
    assert seen == {"pages": pages, "duplex": True, "title": "paper-clip 3 pages"}


def test_print_command_rejects_a_missing_page_and_unknown_paper(monkeypatch, tmp_path: Path) -> None:
    called = {"hit": False}
    monkeypatch.setattr(
        "cli.print_cmd.print_pages",
        lambda *args, **kwargs: called.__setitem__("hit", True) or [1],
    )
    with pytest.raises(typer.Exit):
        print_command([tmp_path / "missing.png"], "ipp://printer.example/ipp/print", "A4", True)
    page = _page(tmp_path, "page.png")
    with pytest.raises(typer.Exit):
        print_command([page, tmp_path / "missing.png"], "ipp://printer.example/ipp/print", "A4", True)
    with pytest.raises(typer.Exit):
        print_command([page], "ipp://printer.example/ipp/print", "Tabloid", False)
    assert called["hit"] is False


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


def test_tui_print_threads_the_duplex_option(monkeypatch, tmp_path: Path) -> None:
    pages = (_page(tmp_path, "page_001.png"), _page(tmp_path, "page_002.png"))
    seen: dict[str, object] = {}

    def fake_print(
        uri: str,
        got: list[Path],
        title: str,
        paper: str = "A4",
        duplex: bool = False,
    ) -> list[int]:
        seen["pages"] = got
        seen["duplex"] = duplex
        seen["paper"] = paper
        seen["title"] = title
        return [4]

    monkeypatch.setattr("cli.tui.print_form.print_pages", fake_print)
    job = PrintJob("job-1", "notes.txt", "now", "A4", pages)
    enabled = submit_print_job("ipp://printer.example/ipp/print", job, True)
    assert seen == {
        "pages": list(pages),
        "duplex": True,
        "paper": "A4",
        "title": "paper-clip job-1",
    }
    assert "both sides" in enabled
    disabled = submit_print_job("ipp://printer.example/ipp/print", job, False)
    assert seen["duplex"] is False
    assert disabled == "[bold green]Submitted 1 page(s) to ipp://printer.example/ipp/print. Job IDs: 4[/bold green]"


def _page(directory: Path, name: str) -> Path:
    path = directory / name
    path.write_bytes(b"png")
    return path
