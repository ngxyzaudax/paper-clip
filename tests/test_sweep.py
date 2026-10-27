import numpy as np

from common.config import resolve_config
from common.page_layout import grid_dimensions, valid_cells_ordered
from scan_sim.sweep import case_seed, run_sweep
from scan_sim.sweep_score import expected_symbols


def test_case_seed_is_stable_and_distinct() -> None:
    assert case_seed(160, 3, 0.5, 1) == 8_863_003_500
    assert case_seed(160, 3, 0.5, 2) != case_seed(160, 3, 0.5, 1)
    assert case_seed(64, 3, 0.5, 1) != case_seed(160, 3, 0.5, 1)


def test_expected_symbols_keep_the_written_prefix() -> None:
    config = resolve_config(paper_size="A6", print_dpi=360, cell_size_px=18, margin_mm=10, num_symbols=5)
    cols, rows = grid_dimensions(config)
    grid = [[-1] * cols for _ in range(rows)]
    for index, (row, col) in enumerate(valid_cells_ordered(config)[:5]):
        grid[row][col] = index % 5
    assert expected_symbols(grid, config) == [0, 1, 2, 3, 4]


def test_clean_sweep_sample_is_reproducible() -> None:
    kwargs = {"samples": 1, "strengths": (0.0,), "sizes": (64,), "decoders": ("colour",)}
    first = run_sweep(**kwargs)[0]
    second = run_sweep(**kwargs)[0]
    assert first._replace(seconds=0.0, mean_seconds=0.0) == second._replace(seconds=0.0, mean_seconds=0.0)
    assert first.ok == 1
    assert first.located == 1
    assert first.symbol_total > 0
    assert first.symbol_error_rate < 0.01
    assert np.isfinite(first.mean_seconds)
