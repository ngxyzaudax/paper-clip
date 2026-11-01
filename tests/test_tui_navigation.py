import asyncio
from pathlib import Path

import pytest

from cli.tui.app import PaperClipApp
from cli.tui.calibrate_screen import CalibrateScreen
from cli.tui.decode_screen import DecodeScreen
from cli.tui.devices_screen import DevicesScreen
from cli.tui.encode_screen import EncodeScreen
from cli.tui.nav_messages import OpenPanel
from cli.tui.print_form import PrintForm
from cli.tui.print_jobs import PrintJob
from cli.tui.print_screen import PrintScreen
from cli.tui.scan_screen import ScanScreen

_PANELS = (EncodeScreen, PrintScreen, ScanScreen, DecodeScreen, DevicesScreen, CalibrateScreen)
_JOBS = [
    PrintJob("job-new", "new.txt", "", "A4", (Path("a.png"),)),
    PrintJob("job-old", "old.txt", "", "A4", (Path("b.png"),)),
]


@pytest.fixture(autouse=True)
def offline_devices(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    form = PrintForm([], _JOBS, [], [("new", "job-new"), ("old", "job-old")], None, "job-new")
    monkeypatch.setattr("cli.tui.print_screen.load_print_form", lambda: form)
    monkeypatch.setattr("cli.tui.scan_screen_workers.discover_scanners_for_scan", lambda: ([], None))
    monkeypatch.setattr("cli.tui.devices_screen.discover_printers", lambda found: ([], None))
    monkeypatch.setattr("cli.tui.devices_screen.discover_scanners", lambda found: ([], None))
    monkeypatch.setattr("cli.tui.decode_screen.discover_scan_jobs", lambda: [])
    monkeypatch.setattr("calibration.sheet_session.session_dir", lambda: tmp_path / "session")


def test_number_keys_open_every_panel() -> None:
    asyncio.run(_number_keys())


def test_encode_handoff_preselects_the_print_job() -> None:
    asyncio.run(_handoff_to_print())


async def _number_keys() -> None:
    async with PaperClipApp().run_test(size=(150, 45)) as pilot:
        await pilot.pause()
        for index, panel in enumerate(_PANELS, 1):
            await pilot.press(str(index))
            await pilot.pause(0.2)
            assert pilot.app.screen.query(panel), panel.__name__


async def _handoff_to_print() -> None:
    async with PaperClipApp().run_test(size=(150, 45)) as pilot:
        await pilot.pause()
        pilot.app.screen.query_one(EncodeScreen).post_message(OpenPanel("nav-print", "job-old"))
        await pilot.pause(0.3)
        assert pilot.app.screen.query_one(PrintScreen)._job_id == "job-old"
