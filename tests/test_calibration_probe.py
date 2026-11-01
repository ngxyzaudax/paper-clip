import numpy as np

import common.device_config as device_config
from calibration.profile import load_density_profile
from calibration.sheet_sim import simulate_limits


def test_simulation_does_not_save_a_profile(monkeypatch, tmp_path) -> None:
    path = tmp_path / "devices.json"
    path.write_text(
        '{"printer": {"name": "Desk", "uri": "", "dpi": 0, "paper_size": "A4", "profile": {}},'
        ' "scanner": {"device": "", "dpi": 1200, "mode": "Color"}}'
    )
    monkeypatch.setattr(device_config, "DEVICE_CONFIG_FILE", path)
    monkeypatch.setattr(device_config, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr("calibration.sheet_sim.draw_side", lambda side: np.zeros((8, 8, 3), np.uint8))
    monkeypatch.setattr(
        "calibration.sheet_sim.apply_scan_augment",
        lambda image, strength, dpi, rng: image,
    )
    monkeypatch.setattr("calibration.sheet_sim.score_page", lambda image: ("front", ()))
    text = simulate_limits((0.3, 0.6, 1.0))
    assert "strength 0.3" in text
    assert "strength 1.0" in text
    assert load_density_profile() is None
