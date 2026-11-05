from pathlib import Path

import pytest
from typer.testing import CliRunner

from calibration.scan_record import ScanRecord
from calibration.session_view import SessionView
from cli.app import app
from workflows.device_pick import dpi_to_use, scanner_to_use
from workflows.calibrate_actions import scan_view
from common.mdns_parse import Service
from common.sane_scan import _chosen_resolution
from common.types import ScannerCapabilities, ScannerInfo


def test_calibrate_scan_uses_the_maximum_when_dpi_is_omitted(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    seen = _capture(monkeypatch, tmp_path, 2400)
    result = CliRunner().invoke(app, ["calibrate", "scan", "--now"])
    assert result.exit_code == 0, result.output
    assert seen == {"device": "https://scanner.test", "dpi": 2400}
    assert "2400 dpi" in result.output


def test_calibrate_scan_honors_an_explicit_dpi(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    seen = _capture(monkeypatch, tmp_path, _refuse)
    result = CliRunner().invoke(app, ["calibrate", "scan", "--now", "--dpi", "300"])
    assert result.exit_code == 0, result.output
    assert seen["dpi"] == 300
    assert "300 dpi" in result.output


def test_tui_scan_view_uses_the_same_maximum(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    seen: dict[str, object] = {}
    monkeypatch.setattr("workflows.device_pick.saved_scanner_uri", lambda: "https://scanner.test")
    monkeypatch.setattr("workflows.device_pick.resolve_max_dpi", lambda device: 2400)
    monkeypatch.setattr("workflows.calibrate_actions.next_scan_path", lambda: tmp_path / "scan-01.png")
    monkeypatch.setattr("workflows.calibrate_actions.capture_page", lambda device, target, dpi: seen.update(device=device, dpi=dpi))
    monkeypatch.setattr("workflows.calibrate_actions.scan_record", lambda path: ScanRecord(path.name, "back", 0, (1,)))
    text = scan_view()
    assert seen == {"device": "https://scanner.test", "dpi": 2400}
    assert "back" in text and "2400 dpi" in text


def test_dpi_to_use_asks_escl_and_sane_devices_for_the_maximum(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[str] = []

    def resolve(device: str) -> int:
        seen.append(device)
        return 2400 if device.startswith("https://") else 1200

    monkeypatch.setattr("workflows.device_pick.resolve_max_dpi", resolve)
    assert dpi_to_use("https://scanner.test", None) == 2400
    assert dpi_to_use("epson2:net:192.0.2.8", None) == 1200
    assert dpi_to_use("https://scanner.test", 300) == 300
    assert seen == ["https://scanner.test", "epson2:net:192.0.2.8"]


def test_linux_keeps_the_literal_address(monkeypatch: pytest.MonkeyPatch) -> None:
    _discover(monkeypatch, "linux")
    monkeypatch.setattr("workflows.device_pick._tcp_open", _refuse)
    assert scanner_to_use() == "https://192.0.2.8:443"


def test_mac_uses_the_hostname_when_it_answers(monkeypatch: pytest.MonkeyPatch) -> None:
    _discover(monkeypatch, "darwin")
    monkeypatch.setattr("workflows.device_pick._tcp_open", lambda uri: "EPSON5CD187.local" in uri)
    assert scanner_to_use() == "https://EPSON5CD187.local:443"


def test_mac_keeps_the_address_when_only_that_answers(monkeypatch: pytest.MonkeyPatch) -> None:
    _discover(monkeypatch, "darwin")
    monkeypatch.setattr("workflows.device_pick._tcp_open", lambda uri: uri.startswith("https://192.0.2.8"))
    assert scanner_to_use() == "https://192.0.2.8:443"


def test_saved_sane_device_is_used(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("workflows.device_pick.saved_scanner_uri", lambda: "")
    monkeypatch.setattr("workflows.device_pick.get_scanner_settings", lambda: {"device": "epson2:libusb:001:004", "dpi": 600})
    assert scanner_to_use() == "epson2:libusb:001:004"


def test_sane_resolution_honors_an_explicit_dpi_and_defaults_to_the_maximum() -> None:
    caps = ScannerCapabilities([300, 1200, 2400], ["Color"], ["Flatbed"])
    assert _chosen_resolution(caps, None) == 2400
    assert _chosen_resolution(caps, 300) == 300
    assert _chosen_resolution(caps, 2400) == 2400


def _capture(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, maximum: object) -> dict[str, object]:
    seen: dict[str, object] = {}
    monkeypatch.setattr("workflows.device_pick.saved_scanner_uri", lambda: "https://scanner.test")
    monkeypatch.setattr("workflows.device_pick.resolve_max_dpi", maximum if callable(maximum) else lambda _device: maximum)
    monkeypatch.setattr("cli.calibrate_cmd.capture_page", lambda device, _target, dpi: seen.update(device=device, dpi=dpi))
    monkeypatch.setattr("cli.calibrate_cmd.next_scan_path", lambda: tmp_path / "scan-01.png")
    monkeypatch.setattr("cli.calibrate_cmd.session_records", lambda: ())
    monkeypatch.setattr("cli.calibrate_cmd.scan_record", lambda path: ScanRecord(path.name, "front", 180, (1,)))
    monkeypatch.setattr("cli.calibrate_cmd.session_view", lambda: _view())
    return seen


def _discover(monkeypatch: pytest.MonkeyPatch, platform: str) -> None:
    service = Service("_uscan._tcp.local", "ET-8500", "EPSON5CD187.local", 443, ("192.0.2.8",), {})
    info = ScannerInfo("https://192.0.2.8:443", "EPSON", "ET-8500", "escl")
    monkeypatch.setattr("workflows.device_pick.saved_scanner_uri", lambda: "")
    monkeypatch.setattr("workflows.device_pick.get_scanner_settings", lambda: {"device": "", "dpi": 1200})
    monkeypatch.setattr("workflows.device_pick.list_escl_scanners", lambda timeout=1.6: [info])
    monkeypatch.setattr("workflows.device_pick.list_scanners", lambda: [])
    monkeypatch.setattr("workflows.device_pick.last_uscan_services", lambda: (service,))
    monkeypatch.setattr("workflows.device_pick.sys.platform", platform)


def _view() -> SessionView:
    return SessionView((), "Turn the FRONT 180 degrees on the glass and scan again.", (), (), None)


def _refuse(_device: str) -> int:
    raise AssertionError(_device)
