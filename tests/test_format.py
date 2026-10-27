import base64

import pytest

from common.codec import calculate_ecc_symbols
from common.config import BLOCK_SIZE, default_config, resolve_config
from common.drawing import dot_radius_px
from common.format_spec import HEADER_BODY, HEADER_STRUCT
from common.geometry import page_geometry
from common.page_layout import data_capacity_bytes
from serialization.encode.encoder import prepare_payload
from serialization.encode.qr_header import decode_header_bytes, encode_header_bytes, qr_image


def test_header_struct_is_78_bytes() -> None:
    assert HEADER_BODY.size == 74
    assert HEADER_STRUCT.size == 78


def test_header_roundtrip_carries_length_dpi_and_hash() -> None:
    config = resolve_config(paper_size="A6", print_dpi=360, cell_size_px=18, margin_mm=10)
    raw = b"paper-clip header"
    prepared = prepare_payload(raw, config, "notes.txt", None)
    blob = encode_header_bytes(
        config, 1, 3, 2, len(prepared.payload), prepared.original_length,
        prepared.original_sha256, prepared.flags,
    )
    header = decode_header_bytes(blob)
    assert header.format_version == 2
    assert header.print_dpi == 360
    assert header.cell_size_px == 18
    assert header.margin_left_mm == 10
    assert header.page_width_mm == 105
    assert header.payload_length == len(prepared.payload)
    assert header.original_length == len(raw)
    assert header.original_sha256 == prepared.original_sha256
    assert header.ecc_sym == calculate_ecc_symbols(BLOCK_SIZE, config.rs_redundancy)
    assert len(base64.b64encode(blob)) <= 122


def test_qr_image_is_native_module_size() -> None:
    config = resolve_config(paper_size="A6", print_dpi=360, cell_size_px=18, margin_mm=10)
    geometry = page_geometry(config)
    blob = encode_header_bytes(config, 0, 1, 1, 240, 4, b"\x00" * 32, 0)
    image = qr_image(blob, config.print_dpi)
    assert image.size == (geometry.qr.width, geometry.qr.height)


def test_default_page_fits_tags_margin_and_cell() -> None:
    config = default_config()
    geometry = page_geometry(config)
    margin_mm = geometry.origin_x * 25.4 / config.print_dpi
    cell_mm = config.cell_size_px * 25.4 / config.print_dpi
    assert margin_mm >= 12
    assert cell_mm >= 0.6
    assert len(geometry.tags) >= 8
    assert geometry.tag_rows >= 2 and geometry.tag_cols >= 2
    assert data_capacity_bytes(config) > 0
    assert dot_radius_px(config.cell_size_px) * 2 < config.cell_size_px


def test_small_test_page_has_capacity() -> None:
    config = resolve_config(paper_size="A6", print_dpi=360, cell_size_px=18, margin_mm=10)
    geometry = page_geometry(config)
    assert len(geometry.tags) >= 4
    assert data_capacity_bytes(config) > 200


def test_cell_below_minimum_millimetre_is_rejected() -> None:
    with pytest.raises(ValueError):
        resolve_config(cell_size_px=10, print_dpi=1200)
