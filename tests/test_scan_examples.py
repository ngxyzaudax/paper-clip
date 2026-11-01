from pathlib import Path

import numpy as np

from common.config import resolve_config
from common.geometry import page_geometry
from ml.real_batch import prepare_page, sample_real_batch
from ml.scan_labels import labels_from_render
from serialization.encode.encoder import payload_to_symbol_grids, prepare_payload
from serialization.encode.pipeline import render_pages


def test_render_labels_match_written_symbols(tmp_path: Path) -> None:
    config = resolve_config(paper_size="A6", print_dpi=360, cell_size_px=18, margin_mm=10, num_symbols=5)
    source = tmp_path / "note.bin"
    source.write_bytes(b"labels")
    prepared = prepare_payload(source.read_bytes(), config, filename=source.name)
    image = np.asarray(render_pages(source, config, prepared=prepared)[0])
    labels = labels_from_render(image, page_geometry(config), config)
    grid = np.asarray(payload_to_symbol_grids(prepared.payload, config, 1)[0])
    assert np.array_equal(labels[grid >= 0], grid[grid >= 0])
    assert np.all(labels[(grid < 0) & (labels >= 0)] == 0)


def test_real_batch_uses_only_complete_windows() -> None:
    labels = np.zeros((16, 16), np.int16)
    labels[:, 8] = -1
    image = np.full((16 * 16, 16 * 16, 3), 255, np.uint8)
    page = prepare_page(image, labels)
    assert len(page.train_origins)
    assert np.all(labels[page.train_origins[:, 0], page.train_origins[:, 1]] >= 0)
    images, sampled, offsets = sample_real_batch([page], 2, np.random.default_rng(1))
    assert images.shape == (2, 96, 96, 3)
    assert sampled.shape == (2, 6, 6)
    assert offsets.shape == (2, 6, 6, 2)
    assert np.all(sampled >= 0)
