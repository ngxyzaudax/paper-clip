import common.device_config as device_config
from calibration.profile import load_density_profile, save_density_profile
from cli.encoding_cli import cli_encoding_config
from common.config import resolve_config
from common.format_spec import FLAG_USER_PASSPHRASE
from common.geometry_measure import mm_to_px
from common.geometry_tags import tag_pixel_size, tag_quiet_px
from common.page_layout import data_capacity_bytes
from common.tag_scale import flags_with_tag_mm, tag_mm_from_flags


def test_tag_pixels_scale_from_the_eight_millimetre_grid() -> None:
    raw = max(40, mm_to_px(8.0, 720))
    base = max(40, (raw // 10) * 10)
    assert tag_pixel_size(720) == base
    assert tag_pixel_size(720, 8.0) == base
    assert tag_quiet_px(720, 8.0) == tag_quiet_px(720)
    assert tag_pixel_size(720, 4.0) == max(16, int(round(base * 0.5)))
    assert tag_quiet_px(720, 4.0) < tag_quiet_px(720)


def test_tag_scale_starts_at_eight_millimetres() -> None:
    assert tag_mm_from_flags(0) == 8.0
    assert tag_mm_from_flags(FLAG_USER_PASSPHRASE) == 8.0
    marked = flags_with_tag_mm(FLAG_USER_PASSPHRASE, 4.0)
    assert marked & FLAG_USER_PASSPHRASE
    assert tag_mm_from_flags(marked) == 4.0
    assert flags_with_tag_mm(0, 8.0) == 0


def test_smaller_tags_hold_more_on_the_same_page() -> None:
    base = data_capacity_bytes(resolve_config(tag_size_mm=8.0))
    dense = data_capacity_bytes(resolve_config(tag_size_mm=4.0))
    assert dense > base


def test_profile_fills_omitted_encode_settings(monkeypatch, tmp_path) -> None:
    path = tmp_path / "devices.json"
    path.write_text(
        '{"printer": {"name": "Desk", "uri": "", "dpi": 0, "paper_size": "A4", "profile": {"note": "later"}},'
        ' "scanner": {"device": "", "dpi": 1200, "mode": "Color"}}'
    )
    monkeypatch.setattr(device_config, "DEVICE_CONFIG_FILE", path)
    monkeypatch.setattr(device_config, "CONFIG_DIR", tmp_path)
    config = resolve_config(cell_size_px=32, num_symbols=5, tag_size_mm=4.0, print_dpi=720)
    save_density_profile(config, 12.5)
    loaded = load_density_profile()
    assert loaded is not None
    assert loaded.tag_size_mm == 4.0
    assert loaded.cell_size_px == config.cell_size_px
    chosen = cli_encoding_config(None, None, None, None, None, None)
    assert chosen.cell_size_px == config.cell_size_px
    assert chosen.num_symbols == config.num_symbols
    assert chosen.tag_size_mm == 4.0
    assert chosen.print_dpi == 720
    explicit = cli_encoding_config(None, 32, None, None, None, None, tag_size_mm=8.0)
    assert explicit.cell_size_px == 32
    assert explicit.tag_size_mm == 8.0
    stored = device_config.load_device_config()
    assert stored["printer"]["name"] == "Desk"
    assert stored["printer"]["profile"]["note"] == "later"
    assert loaded.qr_module_mm == config.qr_module_mm
    assert loaded.dot_ratio == config.dot_ratio
