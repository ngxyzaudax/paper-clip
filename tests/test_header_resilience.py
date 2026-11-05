import os

import numpy as np

from common.config import PaperClipConfig, resolve_config
from common.geometry import page_geometry
from common.geometry_shift import touches
from common.header_cells import split_cells
from common.page_bytes import symbol_count_for_bytes
from common.page_layout import data_capacity_bytes, data_capacity_symbols
from common.symbols import chunk_params
from scan_sim import apply_colour_cast
from scan_sim.render import render_arrays
from serialization.decode.pipeline import decode, decode_document
from serialization.encode.fit_ecc import fill_config
from serialization.encode.grid_header import grid_header_payload
from serialization.encode.header_bytes import encode_header_bytes
from serialization.decode.grid_codec import header_from_grid_bytes


def _config() -> PaperClipConfig:
    return resolve_config(paper_size="A6", print_dpi=360, cell_size_px=18, margin_mm=10)


def _paint(image: np.ndarray, config: PaperClipConfig, region) -> np.ndarray:
    geometry = page_geometry(config)
    painted = image.copy()
    x = geometry.origin_x + region.x
    y = geometry.origin_y + region.y
    painted[y:y + region.height, x:x + region.width] = 0
    return painted


def _paint_qrs(image: np.ndarray, config: PaperClipConfig, indexes: tuple[int, ...]) -> np.ndarray:
    painted = image
    for index in indexes:
        painted = _paint(painted, config, page_geometry(config).slots[index].qr)
    return painted


def _paint_header_cells(image: np.ndarray, config: PaperClipConfig) -> np.ndarray:
    geometry = page_geometry(config)
    painted = image.copy()
    for row, col in split_cells(config)[0]:
        top = geometry.origin_y + row * geometry.cell
        left = geometry.origin_x + col * geometry.cell
        painted[top:top + geometry.cell, left:left + geometry.cell] = 0
    return painted


def test_one_qr_copy_is_enough() -> None:
    config = _config()
    raw = os.urandom(180)
    page = render_arrays(raw, config, "copies.bin")[0]
    painted = _paint_qrs(page, config, (0, 1, 2))
    decoded = decode_document([painted], use_model=False)
    assert decoded.raw == raw
    assert decoded.observed[0].header_source == "qr"
    assert decoded.observed[0].qr_copies_read == 1
    assert "1/4" in decoded.health.header_note
    assert "reprint" in decoded.health.header_note


def test_in_grid_header_survives_when_every_qr_is_painted(monkeypatch) -> None:
    config = _config()
    raw = os.urandom(220)
    fitted = fill_config(raw, config, "grid.bin")
    page = render_arrays(raw, config, "grid.bin")[0]
    monkeypatch.setattr("serialization.decode.header_candidates.stored_configs", lambda: (fitted,))
    decoded = decode_document([_paint_qrs(page, fitted, (0, 1, 2, 3))], use_model=False)
    assert decoded.raw == raw
    assert decoded.observed[0].header_source == "grid"
    assert decoded.observed[0].qr_copies_read == 0
    assert "grid" in decoded.health.header_note
    assert "reprint" in decoded.health.header_note


def test_a_page_with_no_header_is_inferred_from_its_sibling() -> None:
    config = _config()
    raw = os.urandom(data_capacity_bytes(config))
    pages = render_arrays(raw, config, "sibling.bin")
    assert len(pages) >= 2
    blinded = _paint_header_cells(_paint_qrs(pages[1], config, (0, 1, 2, 3)), config)
    decoded = decode_document([pages[0], blinded], use_model=False)
    assert decoded.raw == raw
    orphan = [page for page in decoded.observed if page.header_source == "orphan"]
    assert len(orphan) == 1
    assert orphan[0].header.page_index == 1
    assert orphan[0].inferred_from == 0
    assert "orphan from p1" in decoded.health.header_note


def test_one_wiped_calibration_strip_still_decodes() -> None:
    config = _config()
    raw = os.urandom(160)
    page = render_arrays(raw, config, "strip.bin")[0]
    cast = apply_colour_cast(page, 0.7, np.random.default_rng(4))
    wiped = _paint(cast, config, page_geometry(config).slots[0].calibration)
    recovered, name = decode([wiped], use_model=False)
    assert name == "strip.bin"
    assert recovered == raw


def test_grid_header_bytes_survive_a_destroyed_copy() -> None:
    config = _config()
    blob = encode_header_bytes(config, 1, 2, 2, 400, 20, b"\xab" * 32, 0)
    payload = grid_header_payload(blob)
    size = len(payload) // 2
    broken = bytes(size) + payload[size:]
    header = header_from_grid_bytes(broken, list(range(size)))
    assert header is not None
    assert header.page_index == 1
    assert header.original_sha256 == b"\xab" * 32


def test_slots_stay_clear_of_tags_and_capacity_matches_data_cells() -> None:
    config = _config()
    geometry = page_geometry(config)
    assert len(geometry.tags) >= 4
    blocks = [slot.block for slot in geometry.slots]
    for index, block in enumerate(blocks):
        for other in blocks[index + 1:]:
            assert not touches(
                (block.x, block.y, block.width, block.height),
                (other.x, other.y, other.width, other.height),
            )
    header, data = split_cells(config)
    assert header and set(header).isdisjoint(data)
    assert data_capacity_symbols(config) == len(data)
    k, m = chunk_params(config.num_symbols)
    assert data_capacity_bytes(config) == (len(data) // m) * k
    assert len(header) == symbol_count_for_bytes(len(grid_header_payload(b"\x00" * 78)), config.num_symbols)
