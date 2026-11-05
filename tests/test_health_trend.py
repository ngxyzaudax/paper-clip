from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from typer.testing import CliRunner

from cli.app import app
from health.damage_map import empty_map
from health.pages import PageHealth
from health.reading import Reading, Tracked
from health.report import HealthReport
from health.status import status_of
from health.store import load_tracked, record_reading
from health.trend import trend_of

SHA = "ab" * 32
START = datetime(2026, 1, 1, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def health_store(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr("health.store.HEALTH_DIR", tmp_path / "health")


def _report(health: float, lost: bool = False, rebuilt: bool = False) -> HealthReport:
    page = PageHealth(0, 10, 1000, rebuilt, empty_map())
    return HealthReport(health, health, 4, 50, 20, 10, 1000, (page,), (), 0, lost)


def _reading(days: float, health: float) -> Reading:
    return Reading((START + timedelta(days=days)).isoformat(), "scan", "cell model", _report(health))


def test_bands_follow_the_repair_margin() -> None:
    assert status_of(_report(90.0)).label == "Healthy"
    assert status_of(_report(40.0)).label == "Worn"
    assert status_of(_report(20.0)).label == "At risk"
    assert status_of(_report(5.0)).label == "Critical"
    assert status_of(_report(0.0, lost=True)).label == "Lost"
    assert status_of(_report(90.0, rebuilt=True)).label == "At risk"


def test_trend_projects_when_the_paper_reaches_the_reprint_level() -> None:
    history = Tracked(SHA, "a.bin", 10, (_reading(0, 95.0), _reading(100, 85.0), _reading(200, 75.0)))
    trend = trend_of(history)
    assert trend.since_previous == -10.0
    assert trend.since_first == -20.0
    assert trend.per_year == pytest.approx(-36.5, abs=0.1)
    assert trend.reaches_target is not None
    assert trend.reaches_target.date() == (START + timedelta(days=600)).date()


def test_readings_within_a_day_do_not_project() -> None:
    history = Tracked(SHA, "a.bin", 10, (_reading(0, 95.0), _reading(0.1, 60.0)))
    assert trend_of(history).per_year is None


def test_history_survives_a_round_trip_and_keeps_the_name() -> None:
    record_reading(SHA, "a.bin", 10, _reading(0, 95.0))
    record_reading(SHA, "", 10, _reading(1, 90.0))
    stored = load_tracked(SHA)
    assert stored is not None and stored.filename == "a.bin"
    assert [reading.report.health for reading in stored.readings] == [95.0, 90.0]
    assert stored.readings[0].report.pages[0].damage_map == empty_map()


def test_cli_lists_and_shows_tracked_paper() -> None:
    record_reading(SHA, "a.bin", 10, _reading(0, 95.0))
    record_reading(SHA, "a.bin", 10, _reading(30, 70.0))
    runner = CliRunner()
    listed = runner.invoke(app, ["health"])
    assert listed.exit_code == 0 and "a.bin" in listed.output and "70.0%" in listed.output
    shown = runner.invoke(app, ["health", "show", "a.bin"])
    assert shown.exit_code == 0 and "-25.0" in shown.output and "Advice" in shown.output
    missing = runner.invoke(app, ["health", "show", "nothing"])
    assert missing.exit_code == 1
    forgot = runner.invoke(app, ["health", "forget", "a.bin", "--yes"])
    assert forgot.exit_code == 0 and load_tracked(SHA) is None
