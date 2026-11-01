from dataclasses import replace

from common.config import default_config
from common.dot_ratio import pack_cell_field, unpack_cell_field
from common.format_spec import FLAG_USER_PASSPHRASE
from common.geometry_qr import qr_module_px, qr_side_px
from common.qr_scale import flags_with_qr_mm, qr_mm_from_flags
from serialization.decode.header_config import config_from_header
from serialization.encode.qr_header import decode_header_bytes, encode_header_bytes


def test_legacy_flags_keep_the_qr_module() -> None:
    assert qr_mm_from_flags(0) == 0.36
    assert qr_mm_from_flags(FLAG_USER_PASSPHRASE) == 0.36
    marked = flags_with_qr_mm(FLAG_USER_PASSPHRASE, 0.25)
    assert marked & FLAG_USER_PASSPHRASE
    assert qr_mm_from_flags(marked) == 0.25
    assert flags_with_qr_mm(0, 0.36) == 0


def test_legacy_cell_field_keeps_the_dot_ratio() -> None:
    assert unpack_cell_field(32) == (32, 0.62)
    packed = pack_cell_field(22, 0.50)
    assert unpack_cell_field(packed) == (22, 0.50)
    assert packed & 0x0FFF == 22


def test_header_roundtrip_carries_qr_module_and_dot_ratio() -> None:
    config = default_config()
    blob = encode_header_bytes(config, 0, 1, 1, 10, 4, b"\x11" * 32, flags_with_qr_mm(0, 0.30))
    smaller = config_from_header(decode_header_bytes(blob))
    assert smaller.qr_module_mm == 0.30
    assert smaller.dot_ratio == 0.62
    assert smaller.cell_size_px == config.cell_size_px
    tight_blob = encode_header_bytes(
        replace(default_config(), dot_ratio=0.50),
        0, 1, 1, 10, 4, b"\x11" * 32, 0,
    )
    assert config_from_header(decode_header_bytes(tight_blob)).dot_ratio == 0.50


def test_smaller_qr_module_draws_a_smaller_code() -> None:
    assert qr_side_px(720, 0.25) < qr_side_px(720, 0.36)
    assert qr_module_px(720, 0.36) == qr_module_px(720)
