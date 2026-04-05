import logging
import time
from collections.abc import Iterator
from contextlib import contextmanager


@contextmanager
def log_phase(logger: logging.Logger, label: str) -> Iterator[None]:
    t0 = time.perf_counter()
    yield
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    logger.debug("%s duration_ms=%.2f", label, elapsed_ms)
