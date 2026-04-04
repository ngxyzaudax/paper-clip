import json
from pathlib import Path

import cv2
import numpy as np
from skimage.metrics import structural_similarity

from detect_corners import (
    CornerDetection,
    detect_corners_oriented,
)


GROUND_TRUTH_PATH = Path(__file__).parent / "ground_truth.json"
CHART_PATH = Path(__file__).parent / "calibration_chart.png"
SCANS_DIR = Path(__file__).parent / "scans"
OUTPUT_DIR = Path(__file__).parent / "output" / "aligned"

TAG_REGION_HALF = 150


def _load_ground_truth() -> dict:
    return json.loads(GROUND_TRUTH_PATH.read_text())


def _compute_homography(detections: list[CornerDetection]) -> np.ndarray:
    src = np.float32([[d.scan_x, d.scan_y] for d in detections])
    dst = np.float32([[d.chart_x, d.chart_y] for d in detections])
    method = cv2.RANSAC if len(src) > 4 else 0
    H, _ = cv2.findHomography(src, dst, method)
    if H is None:
        raise ValueError("Homography computation failed")
    return H


def warp_scan_to_chart(
    scan: np.ndarray,
    homography: np.ndarray,
    chart_width: int,
    chart_height: int,
) -> np.ndarray:
    return cv2.warpPerspective(
        scan, homography, (chart_width, chart_height),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(255, 255, 255),
    )


def _ssim_at_region(
    aligned: np.ndarray, chart: np.ndarray, cx: int, cy: int, half: int,
) -> float:
    h, w = chart.shape[:2]
    y1, y2 = max(0, cy - half), min(h, cy + half)
    x1, x2 = max(0, cx - half), min(w, cx + half)
    region_a = cv2.cvtColor(aligned[y1:y2, x1:x2], cv2.COLOR_BGR2GRAY)
    region_c = cv2.cvtColor(chart[y1:y2, x1:x2], cv2.COLOR_BGR2GRAY)
    if region_a.shape != region_c.shape or region_a.size == 0:
        return 0.0
    return float(structural_similarity(region_a, region_c))


def validate_alignment(
    aligned: np.ndarray,
    chart: np.ndarray,
    corners: dict[str, list[int]],
) -> dict[str, float]:
    scores = {}
    for name, (cx, cy) in corners.items():
        scores[name] = _ssim_at_region(aligned, chart, cx, cy, TAG_REGION_HALF)
    scores["mean"] = float(np.mean(list(scores.values())[:4]))
    return scores


def align_scan(
    scan_path: Path,
    chart: np.ndarray,
    chart_gray: np.ndarray,
    gt: dict,
) -> tuple[np.ndarray, dict[str, float], list[CornerDetection], int]:
    scan = cv2.imread(str(scan_path))
    if scan is None:
        raise FileNotFoundError(f"Cannot read {scan_path}")
    scan_gray = cv2.cvtColor(scan, cv2.COLOR_BGR2GRAY)

    orientation_steps, detections = detect_corners_oriented(
        scan_gray, chart_gray, gt["corners"],
    )
    H = _compute_homography(detections)
    aligned = warp_scan_to_chart(scan, H, gt["chart_width"], gt["chart_height"])
    ssim_scores = validate_alignment(aligned, chart, gt["corners"])

    return aligned, ssim_scores, detections, orientation_steps


def align_all_scans(save: bool = True) -> dict[str, dict]:
    gt = _load_ground_truth()
    chart = cv2.imread(str(CHART_PATH))
    chart_gray = cv2.cvtColor(chart, cv2.COLOR_BGR2GRAY)

    if save:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    results = {}
    scan_paths = sorted(SCANS_DIR.glob("scan*.png"))
    for scan_path in scan_paths:
        print(f"Aligning {scan_path.name}...")
        aligned, ssim_scores, detections, orientation_k = align_scan(
            scan_path, chart, chart_gray, gt,
        )

        if save:
            out_path = OUTPUT_DIR / scan_path.name
            cv2.imwrite(str(out_path), aligned)
            print(f"  Saved to {out_path}")

        results[scan_path.name] = {
            "ssim": ssim_scores,
            "corners_detected": sum(1 for d in detections if d.score > 0),
            "orientation_cw_90_steps": orientation_k,
        }
        print(f"  orientation_cw_90_steps={orientation_k}  SSIM: {ssim_scores}")

    return results


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    results = align_all_scans()
    print("\n=== Alignment Summary ===")
    for scan_name, info in results.items():
        mean_ssim = info["ssim"]["mean"]
        status = "OK" if mean_ssim > 0.5 else "WARN"
        print(f"  {scan_name}: mean_SSIM={mean_ssim:.3f}, corners={info['corners_detected']} [{status}]")
