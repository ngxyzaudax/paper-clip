import logging
import sys
from pathlib import Path

from common.data_store import DATA_ROOT

LOG_DIR = DATA_ROOT / "logs"

LOG_FORMAT = "%(asctime)s.%(msecs)03d [%(levelname)-8s] %(name)s: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

LEVEL_FILES: list[tuple[str, int]] = [
    ("debug.log", logging.DEBUG),
    ("info.log", logging.INFO),
    ("warning.log", logging.WARNING),
    ("error.log", logging.ERROR),
]


def _make_handler(path: Path, level: int) -> logging.FileHandler:
    handler = logging.FileHandler(path, mode="w", encoding="utf-8")
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
    return handler


def setup_logging(console: bool = False) -> Path:
    """Configure multi-file logging. Returns the log directory path.

    Each level gets its own standalone file (recreated on every startup).
    When console=True a StreamHandler is added for CLI subcommands;
    omitted when running the TUI to avoid screen corruption.
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    for existing in root.handlers[:]:
        root.removeHandler(existing)

    for filename, level in LEVEL_FILES:
        root.addHandler(_make_handler(LOG_DIR / filename, level))

    if console:
        stderr_handler = logging.StreamHandler(sys.stderr)
        stderr_handler.setLevel(logging.INFO)
        stderr_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
        root.addHandler(stderr_handler)

    logging.getLogger("PIL").setLevel(logging.WARNING)
    logging.getLogger("tensorflow").setLevel(logging.WARNING)
    logging.getLogger("h5py").setLevel(logging.WARNING)

    root.info("Logging initialised — log directory: %s", LOG_DIR.resolve())
    return LOG_DIR
