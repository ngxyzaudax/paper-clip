import math
from dataclasses import replace

import numpy as np

from common.config import PaperClipConfig, resolve_config
from common.format_spec import ECC_MAX
from common.geometry import page_geometry
from common.page_layout import data_capacity_bytes, pages_needed, valid_cells_ordered
from common.types import SymbolGrid
from scan_sim.render import render_document
from serialization.decode.pipeline import decode
from serialization.encode.encoder import payload_byte_length_and_hash
from serialization.encode.fit_ecc import fill_config, largest_ecc
from serialization.encode.frame_payload import interleaved_length
from serialization.encode.stripe import STRIPE


def test_stream_grows_as_parity_grows() -> None:
    previous = 0
    for ecc in range(2, ECC_MAX + 1):
        length = interleaved_length(5000, 8, ecc)
        assert length >= previous
        previous = length


def test_extra_parity_does_not_add_a_page() -> None:
    config = _page()
    blob = _fullest_blob(config)
    pages = pages_needed(interleaved_length(blob, 8, config.ecc_sym), config)
    ecc = largest_ecc(blob, 8, config)
    assert pages_needed(interleaved_length(blob, 8, ecc), config) == pages
    if ecc < ECC_MAX:
        assert pages_needed(interleaved_length(blob, 8, ecc + 1), config) > pages


def test_short_file_fills_with_parity_and_a_black_tail() -> None:
    config = _page()
    raw = b"short-paper-clip"
    name = "short.bin"
    floor_pages = pages_needed(payload_byte_length_and_hash(raw, config, name)[0], config)
    images, prepared, grids = render_document(raw, config, name)
    fitted = fill_config(raw, config, name)
    assert fitted.ecc_sym > config.ecc_sym
    assert pages_needed(len(prepared.payload), fitted) == floor_pages
    assert fill_config(raw, fitted, name).ecc_sym == fitted.ecc_sym
    _assert_next_byte_spills(raw, name, fitted, floor_pages)
    _assert_tail_is_solid_black(images[-1], grids[-1], fitted)
    _assert_forbidden_cells_stay_empty(grids[-1], fitted)
    recovered, decoded_name = decode(images, use_model=False)
    assert decoded_name == name
    assert recovered == raw


def _page() -> PaperClipConfig:
    return resolve_config(paper_size="A6", print_dpi=360, cell_size_px=18, margin_mm=10)


def _fullest_blob(config: PaperClipConfig) -> int:
    capacity = data_capacity_bytes(config)
    best_blob, best_slack = 0, capacity
    for blob in range(capacity * 3 + 1):
        stream = interleaved_length(blob, 8, config.ecc_sym)
        slack = capacity * math.ceil(stream / capacity) - stream
        if slack < best_slack:
            best_blob, best_slack = blob, slack
    return best_blob


def _assert_next_byte_spills(
    raw: bytes, name: str, fitted: PaperClipConfig, floor_pages: int,
) -> None:
    if fitted.ecc_sym >= ECC_MAX:
        return
    higher = replace(fitted, ecc_sym=fitted.ecc_sym + 1)
    length, _hash = payload_byte_length_and_hash(raw, higher, name)
    assert pages_needed(length, higher) > floor_pages


def _assert_tail_is_solid_black(
    image: np.ndarray, grid: SymbolGrid, config: PaperClipConfig,
) -> None:
    geometry = page_geometry(config)
    row, col = _first(grid, STRIPE)
    cell = geometry.cell
    x = geometry.origin_x + col * cell
    y = geometry.origin_y + row * cell
    assert _pixel(image, y, x) == (0, 0, 0)
    assert _pixel(image, y + cell - 1, x + cell - 1) == (0, 0, 0)


def _assert_forbidden_cells_stay_empty(grid: SymbolGrid, config: PaperClipConfig) -> None:
    valid = set(valid_cells_ordered(config))
    for row, cells in enumerate(grid):
        for col, symbol in enumerate(cells):
            if (row, col) not in valid:
                assert symbol == -1


def _first(grid: SymbolGrid, symbol: int) -> tuple[int, int]:
    for row, cells in enumerate(grid):
        for col, value in enumerate(cells):
            if value == symbol:
                return row, col
    raise AssertionError("stripe cell was not marked")


def _pixel(image: np.ndarray, y: int, x: int) -> tuple[int, int, int]:
    red, green, blue = image[y, x]
    return int(red), int(green), int(blue)
