import os

import numpy as np

from common.config import resolve_config
from common.crypto import compute_sha256
from scan_sim import apply_colour_cast, apply_scan_augment
from scan_sim.render import render_arrays
from serialization.decode.pipeline import decode


def _config():
    return resolve_config(paper_size="A6", print_dpi=360, cell_size_px=18, margin_mm=10)


def test_clean_page_roundtrip_matches_sha256() -> None:
    config = _config()
    raw = os.urandom(180)
    pages = render_arrays(raw, config, "clean.bin")
    recovered, name = decode(pages, use_model=False)
    assert name == "clean.bin"
    assert recovered == raw
    assert compute_sha256(recovered) == compute_sha256(raw)


def test_light_augmentation_still_decodes() -> None:
    config = _config()
    raw = os.urandom(160)
    pages = render_arrays(raw, config, "light.bin")
    scans = [
        apply_scan_augment(page, 0.25, config.print_dpi, np.random.default_rng(21))
        for page in pages
    ]
    recovered, name = decode(scans, use_model=False)
    assert name == "light.bin"
    assert recovered == raw


def test_colour_cast_uses_calibration_strip() -> None:
    config = _config()
    raw = os.urandom(140)
    pages = render_arrays(raw, config, "cast.bin")
    scans = [apply_colour_cast(page, 0.7, np.random.default_rng(4)) for page in pages]
    recovered, name = decode(scans, use_model=False)
    assert name == "cast.bin"
    assert recovered == raw


def test_missing_page_is_rebuilt_from_parity() -> None:
    config = resolve_config(
        paper_size="A6", print_dpi=360, cell_size_px=18, margin_mm=10, redundancy_pages=1,
    )
    raw = os.urandom(1800)
    pages = render_arrays(raw, config, "multi.bin")
    assert len(pages) >= 2
    recovered, name = decode(pages[1:], use_model=False)
    assert name == "multi.bin"
    assert recovered == raw


def test_strength_zero_augment_is_a_copy() -> None:
    image = np.full((24, 24, 3), 255, np.uint8)
    image[4:16, 4:16] = (0, 180, 180)
    out = apply_scan_augment(image, 0.0, 360, np.random.default_rng(1))
    assert np.array_equal(out, image)
