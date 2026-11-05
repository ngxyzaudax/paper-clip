import os
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from common.config import PaperClipConfig, resolve_config
from common.geometry import page_geometry
from common.page_layout import valid_cells_ordered
from health.check import run_check
from health.page_cells import page_cell_grid
from health.store import all_tracked, find_tracked, forget_tracked
from scan_sim.render import render_arrays
from serialization.decode.errors import PassphraseError
from serialization.decode.pipeline import decode_document

STRIPE_ROW = 30


@pytest.fixture(autouse=True)
def health_store(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    monkeypatch.setattr("health.store.HEALTH_DIR", tmp_path / "health")
    return tmp_path / "health"


def _config() -> PaperClipConfig:
    return resolve_config(paper_size="A6", print_dpi=360, cell_size_px=18, margin_mm=10)


def _marked(page: np.ndarray, config: PaperClipConfig, rows: int) -> np.ndarray:
    geometry = page_geometry(config)
    marked = page.copy()
    top = geometry.origin_y + STRIPE_ROW * geometry.cell
    right = geometry.origin_x + geometry.cols * geometry.cell
    marked[top:top + rows * geometry.cell, geometry.origin_x:right] = (10, 10, 10)
    return marked


def _ink_data_cells(page: np.ndarray, config: PaperClipConfig, share: float) -> np.ndarray:
    geometry = page_geometry(config)
    inked = page.copy()
    cells = valid_cells_ordered(config)
    for row, col in cells[:int(len(cells) * share)]:
        top, left = geometry.origin_y + row * geometry.cell, geometry.origin_x + col * geometry.cell
        inked[top:top + geometry.cell, left:left + geometry.cell] = (10, 10, 10)
    return inked


def test_marker_damage_lowers_health_and_is_found_where_it_was_drawn() -> None:
    config = _config()
    page = render_arrays(os.urandom(400), config, "marked.bin")[0]
    clean = decode_document([page], use_model=False)
    damaged = decode_document([_marked(page, config, 2)], use_model=False)
    assert 0.0 < damaged.health.health < clean.health.health
    assert damaged.health.damaged_bytes > clean.health.damaged_bytes
    grid = page_cell_grid(damaged.header)
    new = np.setdiff1d(damaged.wrong_cells[0], clean.wrong_cells[0])
    rows = grid[new][:, 0]
    assert np.mean((rows >= STRIPE_ROW) & (rows < STRIPE_ROW + 2)) > 0.9


def test_each_check_is_recorded_with_a_damage_image(health_store: Path) -> None:
    config = _config()
    page = render_arrays(os.urandom(500), config, "tracked.bin")[0]
    first = run_check([page], use_model=False)
    second = run_check([_marked(page, config, 2)], use_model=False)
    assert second.sha256 == first.sha256
    assert len(second.history.readings) == 2
    assert second.history.readings[-1].report.health < second.history.readings[0].report.health
    image = Path(second.reading.damage_image)
    assert image.is_file() and image.is_relative_to(health_store)
    assert Image.open(image).width > 0
    assert find_tracked("tracked.bin").sha256 == first.sha256
    assert find_tracked(first.sha256[:8]).filename == "tracked.bin"


def test_unreadable_paper_is_recorded_as_lost() -> None:
    config = _config()
    page = render_arrays(os.urandom(500), config, "gone.bin")[0]
    run_check([page], use_model=False)
    lost = run_check([_ink_data_cells(page, config, 0.5)], use_model=False)
    assert lost.decoded is None
    assert lost.reading.report.lost and lost.reading.report.health == 0.0
    assert lost.filename == "gone.bin"
    assert [reading.report.lost for reading in lost.history.readings] == [False, True]


def test_check_without_tracking_leaves_the_history_alone() -> None:
    page = render_arrays(os.urandom(300), _config(), "quiet.bin")[0]
    check = run_check([page], use_model=False, track=False)
    assert not check.saved
    assert all_tracked() == []


def test_missing_passphrase_is_not_mistaken_for_lost_paper() -> None:
    pages = render_arrays(b"secret-bytes" * 20, _config(), "secret.bin", passphrase="horse")
    with pytest.raises(PassphraseError):
        run_check(pages, use_model=False)
    assert all_tracked() == []


def test_forget_removes_the_history() -> None:
    page = render_arrays(os.urandom(300), _config(), "forget.bin")[0]
    check = run_check([page], use_model=False)
    assert forget_tracked(check.sha256)
    assert all_tracked() == []
