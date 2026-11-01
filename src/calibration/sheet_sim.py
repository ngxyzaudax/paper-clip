import cv2
import numpy as np

from calibration.sheet_draw import draw_side
from calibration.sheet_limits import axis_limits, choose_profile
from calibration.sheet_place import sheet_side
from calibration.sheet_report import format_limits
from calibration.sheet_score import PatchRead, score_page
from scan_sim.pipeline import apply_scan_augment


def simulate_limits(strengths: tuple[float, ...] = (0.3, 0.6, 1.0)) -> str:
    pages = {name: np.asarray(draw_side(sheet_side(name))) for name in ("front", "back")}
    blocks = [_strength_block(pages, strength) for strength in strengths]
    return "\n\n".join(blocks)


def _strength_block(pages: dict[str, np.ndarray], strength: float) -> str:
    reads: list[PatchRead] = []
    for index, image in enumerate(pages.values()):
        rng = np.random.default_rng(17 + index + int(strength * 100))
        damaged = apply_scan_augment(_stretch(image), strength, 720, rng)
        _side, found = score_page(damaged)
        reads.extend(found)
    chosen = choose_profile(tuple(reads))
    return f"strength {strength:.1f}\n{format_limits(axis_limits(tuple(reads)), chosen)}"


def _stretch(image: np.ndarray, factor: float = 1.03) -> np.ndarray:
    height, width = image.shape[:2]
    return cv2.resize(image, (int(width * factor), height), interpolation=cv2.INTER_LINEAR)
