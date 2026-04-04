import logging
from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


def session_dir(base: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return base / f"scan_{stamp}"


def average_images(paths: list[Path]) -> np.ndarray:
    arrays = [np.array(Image.open(p).convert("RGB"), dtype=np.float32) for p in paths]
    return np.mean(np.stack(arrays), axis=0).astype(np.uint8)


def save_master(paths: list[Path], run_dir: Path) -> Path:
    master_path = run_dir / "master.png"
    if len(paths) == 1:
        import shutil
        shutil.copy2(paths[0], master_path)
        logger.info("Single scan, copied to master: %s", master_path)
        return master_path
    averaged = average_images(paths)
    Image.fromarray(averaged).save(str(master_path), format="PNG", compress_level=1)
    logger.info("Averaged %d scans -> master: %s", len(paths), master_path)
    return master_path
