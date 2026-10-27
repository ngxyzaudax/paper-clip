import os
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import NamedTuple

import numpy as np

from common.config import PaperClipConfig, resolve_config
from scan_sim.pipeline import apply_scan_augment
from scan_sim.render import render_document
from scan_sim.sweep_score import SampleScore, expected_symbols, score_scans

PROTOCOL_SAMPLES = 20
PROTOCOL_STRENGTHS = (0.0, 0.25, 0.5, 0.75, 1.0)
PROTOCOL_BYTES = (64, 160, 400)
PROTOCOL_DECODERS = ("colour", "model")


class SweepRow(NamedTuple):
    strength: float
    nbytes: int
    decoder: str
    samples: int
    ok: int
    success_rate: float
    symbol_errors: int
    symbol_total: int
    symbol_error_rate: float
    erasures: int
    located: int
    mean_erasures: float
    seconds: float
    mean_seconds: float


def sweep_config() -> PaperClipConfig:
    return resolve_config(
        paper_size="A6", print_dpi=360, cell_size_px=18, margin_mm=10, num_symbols=5,
    )


def case_seed(nbytes: int, index: int, strength: float, stream: int) -> int:
    strength_code = int(round(float(strength) * 1000))
    return 8_603_000_000 + stream * 100_000_000 + int(nbytes) * 1_000_000 + index * 1_000 + strength_code


def run_sweep(
    samples: int = PROTOCOL_SAMPLES,
    strengths: tuple[float, ...] = PROTOCOL_STRENGTHS,
    sizes: tuple[int, ...] = PROTOCOL_BYTES,
    decoders: tuple[str, ...] = PROTOCOL_DECODERS,
    config: PaperClipConfig | None = None,
    model_path: str | None = None,
    on_row: Callable[[SweepRow], None] | None = None,
) -> list[SweepRow]:
    page = config or sweep_config()
    model = _model(decoders, model_path)
    rows: list[SweepRow] = []
    for strength in strengths:
        for nbytes in sizes:
            scores = {name: [] for name in decoders}
            for index in range(samples):
                scans, expected, payload = _case(page, nbytes, index, strength)
                for name in decoders:
                    scores[name].append(score_scans(scans, expected, payload, model if name == "model" else None))
            for name in decoders:
                row = _row(strength, nbytes, name, scores[name])
                rows.append(row)
                if on_row is not None:
                    on_row(row)
    return rows


def _case(
    config: PaperClipConfig, nbytes: int, index: int, strength: float,
) -> tuple[list[np.ndarray], list[list[int]], bytes]:
    payload_rng = np.random.default_rng(case_seed(nbytes, index, strength, 1))
    augment_rng = np.random.default_rng(case_seed(nbytes, index, strength, 2))
    crypto_rng = np.random.default_rng(case_seed(nbytes, index, strength, 3))
    payload = payload_rng.integers(0, 256, size=nbytes, dtype=np.uint8).tobytes()
    with _seeded_urandom(crypto_rng):
        images, _prepared, grids = render_document(payload, config, filename=f"sweep-{nbytes}-{index}.bin")
    scans = [_augment(image, strength, config.print_dpi, augment_rng) for image in images]
    return scans, [expected_symbols(grid, config) for grid in grids], payload


@contextmanager
def _seeded_urandom(rng: np.random.Generator) -> Iterator[None]:
    def _bytes(size: int) -> bytes:
        return rng.integers(0, 256, size=size, dtype=np.uint8).tobytes()

    original = os.urandom
    os.urandom = _bytes
    try:
        yield
    finally:
        os.urandom = original


def _augment(image: np.ndarray, strength: float, dpi: int, rng: np.random.Generator) -> np.ndarray:
    page_seed = int(rng.integers(1, 2**31 - 1))
    return apply_scan_augment(image, strength, dpi, np.random.default_rng(page_seed))


def _model(decoders: tuple[str, ...], model_path: str | None) -> object | None:
    if "model" not in decoders:
        return None
    from pathlib import Path

    from ml.store import load_cell_model

    path = Path(model_path) if model_path else None
    return load_cell_model(path, required=True)


def _row(strength: float, nbytes: int, decoder: str, scores: list[SampleScore]) -> SweepRow:
    samples = len(scores)
    ok = sum(1 for score in scores if score.ok)
    symbol_errors = sum(score.symbol_errors for score in scores)
    symbol_total = sum(score.symbol_total for score in scores)
    located_scores = [score for score in scores if score.located and score.erasures is not None]
    erasures = sum(int(score.erasures) for score in located_scores)
    seconds = sum(score.seconds for score in scores)
    rate = ok / samples if samples else 0.0
    symbol_rate = symbol_errors / symbol_total if symbol_total else 0.0
    mean_erasures = erasures / len(located_scores) if located_scores else float("nan")
    mean_seconds = seconds / samples if samples else 0.0
    return SweepRow(
        strength, nbytes, decoder, samples, ok, rate,
        symbol_errors, symbol_total, symbol_rate,
        erasures, len(located_scores), mean_erasures, seconds, mean_seconds,
    )
