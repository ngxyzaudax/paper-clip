import asyncio
from pathlib import Path

import pytest
from textual.app import App, ComposeResult
from textual.widgets import Button, Static

from cli.tui.calibrate_screen import CalibrateScreen
from cli.tui.confirm_screen import ConfirmScreen


@pytest.fixture
def isolated_session(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> list[str]:
    printed: list[str] = []
    monkeypatch.setattr("calibration.sheet_io.calibration_dir", lambda: tmp_path)
    monkeypatch.setattr("calibration.session_state.calibration_dir", lambda: tmp_path)
    monkeypatch.setattr("calibration.sheet_io.session_dir", lambda: tmp_path / "session")
    monkeypatch.setattr("calibration.sheet_session.session_dir", lambda: tmp_path / "session")
    monkeypatch.setattr("cli.tui.calibrate_flow.sheet_ready", lambda: True)
    monkeypatch.setattr("cli.tui.calibrate_flow._saved_or_only_printer", lambda: "ipp://printer.test/ipp/print")
    monkeypatch.setattr("cli.tui.calibrate_flow.print_once", lambda uri: printed.append(uri) or "sent")
    monkeypatch.setattr("cli.tui.calibrate_confirm.print_once", lambda uri: printed.append(uri) or "sent")
    return printed


def test_calibration_panel_shows_steps_and_next_instruction(isolated_session: list[str]) -> None:
    asyncio.run(_shows_steps())


def test_cancelled_print_sends_nothing(isolated_session: list[str]) -> None:
    asyncio.run(_cancel_print())
    assert isolated_session == []


def test_confirmed_print_sends_one_job(isolated_session: list[str]) -> None:
    asyncio.run(_confirm_print())
    assert isolated_session == ["ipp://printer.test/ipp/print"]


async def _shows_steps() -> None:
    async with _Host().run_test(size=(140, 40)) as pilot:
        await _settle(pilot)
        steps = str(pilot.app.query_one("#cal-steps", Static).render())
        assert "Render the sheet" in steps and "Scan both sides (0 of 2)" in steps
        assert not pilot.app.query_one("#cal-scan", Button).disabled


async def _cancel_print() -> None:
    async with _Host().run_test(size=(140, 40)) as pilot:
        await _settle(pilot)
        await pilot.click("#cal-print")
        await _settle(pilot)
        assert isinstance(pilot.app.screen, ConfirmScreen)
        await pilot.click("#confirm-cancel")
        await _settle(pilot)


async def _confirm_print() -> None:
    async with _Host().run_test(size=(140, 40)) as pilot:
        await _settle(pilot)
        await pilot.click("#cal-print")
        await _settle(pilot)
        await pilot.click("#confirm-ok")
        await _settle(pilot)


async def _settle(pilot) -> None:
    for _ in range(40):
        await pilot.pause(0.05)
        panel = pilot.app.query(CalibrateScreen)
        if not panel or not panel.first().busy:
            await pilot.pause()
            return


class _Host(App):
    def compose(self) -> ComposeResult:
        yield CalibrateScreen()
