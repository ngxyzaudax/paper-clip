import asyncio

import pytest
from textual.app import App, ComposeResult
from textual.widgets import Button

from cli.tui.print_form import PrintForm
from cli.tui.print_screen import PrintScreen


def test_print_screen_duplex_control_defaults_off(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "cli.tui.print_screen.load_print_form",
        lambda: PrintForm([], [], [], [], None, None),
    )
    asyncio.run(_duplex_defaults_off())


async def _duplex_defaults_off() -> None:
    app = _Host()
    async with app.run_test(size=(100, 30)) as pilot:
        await pilot.pause()
        screen = pilot.app.query_one(PrintScreen)
        button = pilot.app.query_one("#print-duplex-pick", Button)
        assert screen._duplex is False
        assert _label(button) == "Off"
        assert not button.disabled
        screen._on_option_picked("duplex", "on")
        assert screen._duplex is True
        assert _label(pilot.app.query_one("#print-duplex-pick", Button)) == "On"
        screen._on_option_picked("duplex", "off")
        assert screen._duplex is False
        assert _label(pilot.app.query_one("#print-duplex-pick", Button)) == "Off"


class _Host(App):

    def compose(self) -> ComposeResult:
        yield PrintScreen()


def _label(button: Button) -> str:
    return str(button.label)
