import common.device_config as device_config
from common.device_config import load_device_config, save_printer_settings


def test_legacy_config_gains_uri_and_keeps_profile(monkeypatch, tmp_path) -> None:
    path = tmp_path / "devices.json"
    path.write_text(
        '{"printer": {"name": "old-queue", "dpi": 0, "paper_size": "A4", "profile": {"note": "later"}},'
        ' "scanner": {"device": "airscan:e0:example", "dpi": 600, "mode": "Color"}}'
    )
    monkeypatch.setattr(device_config, "DEVICE_CONFIG_FILE", path)
    monkeypatch.setattr(device_config, "CONFIG_DIR", tmp_path)
    loaded = load_device_config()
    assert loaded["printer"]["uri"] == ""
    assert loaded["printer"]["profile"] == {"note": "later"}
    assert loaded["scanner"]["device"] == "airscan:e0:example"
    assert loaded["scanner"]["uri"] == ""
    save_printer_settings("Desk", "ipp://192.0.2.10:631/ipp/print", paper_size="A4")
    stored = load_device_config()
    assert stored["printer"]["uri"] == "ipp://192.0.2.10:631/ipp/print"
    assert stored["printer"]["profile"] == {"note": "later"}
    assert stored["scanner"]["dpi"] == 600
