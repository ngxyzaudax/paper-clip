import json
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import get_context
from pathlib import Path

import cv2
import numpy as np
from skimage.metrics import structural_similarity

from detect_corners import (
    MATCH_THRESHOLD,
    CornerDetection,
    detect_corners_in_scan,
    detect_corners_oriented,
)
from orientation import map_cw_rotated_to_original
from pool_util import max_cpu_workers


GROUND_TRUTH_PATH = Path(__file__).parent / "ground_truth.json"
CHART_PATH = Path(__file__).parent / "calibration_chart.png"
SCANS_DIR = Path(__file__).parent / "scans"
OUTPUT_DIR = Path(__file__).parent / "output" / "aligned"

TAG_REGION_HALF = 150

_mp_chart_bgr: np.ndarray | None = None
_mp_chart_gray: np.ndarray | None = None
_mp_gt: dict | None = None
_mp_out_dir: Path | None = None
_mp_save_aligned: bool = False
_mp_corners: dict[str, list[int]] | None = None


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


def _mp_align_state_init(
    chart_abs: str, gt_abs: str, out_dir_abs: str, do_save: bool,
) -> None:
    global _mp_chart_bgr, _mp_chart_gray, _mp_gt, _mp_out_dir, _mp_save_aligned, _mp_corners
    cv2.setNumThreads(1)
    chart = cv2.imread(chart_abs)
    if chart is None:
        raise FileNotFoundError(chart_abs)
    _mp_chart_bgr = chart
    _mp_chart_gray = cv2.cvtColor(chart, cv2.COLOR_BGR2GRAY)
    _mp_gt = json.loads(Path(gt_abs).read_text())
    _mp_corners = _mp_gt["corners"]
    _mp_out_dir = Path(out_dir_abs)
    _mp_save_aligned = do_save


def _mp_align_phase1_orient_task(
    spec: tuple[str, int],
) -> tuple[str, int, float, list[CornerDetection]]:
    path_abs, rot_k = spec
    assert _mp_chart_gray is not None and _mp_corners is not None
    scan = cv2.imread(path_abs)
    if scan is None:
        return Path(path_abs).name, rot_k, -1.0, []
    scan_gray = cv2.cvtColor(scan, cv2.COLOR_BGR2GRAY)
    if rot_k == 0:
        rot = scan_gray
    else:
        rot = scan_gray.copy()
        for _ in range(rot_k):
            rot = cv2.rotate(rot, cv2.ROTATE_90_CLOCKWISE)
    dets = detect_corners_in_scan(rot, _mp_chart_gray, _mp_corners, MATCH_THRESHOLD)
    measured = [d for d in dets if d.score > 0]
    if not measured:
        return Path(path_abs).name, rot_k, -1.0, dets
    score = sum(d.score for d in measured) + 0.01 * len(measured)
    return Path(path_abs).name, rot_k, score, dets


def _mp_align_phase2_warp_task(
    spec: tuple[str, int, list[CornerDetection]],
) -> tuple[str, dict[str, float], int, int]:
    path_abs, best_k, dets = spec
    assert _mp_chart_bgr is not None and _mp_gt is not None and _mp_out_dir is not None
    scan_path = Path(path_abs)
    scan = cv2.imread(path_abs)
    if scan is None:
        raise FileNotFoundError(path_abs)
    orig_h, orig_w = scan.shape[:2]
    mapped: list[CornerDetection] = []
    for d in dets:
        ox, oy = map_cw_rotated_to_original(
            d.scan_x, d.scan_y, best_k, orig_w, orig_h,
        )
        mapped.append(CornerDetection(
            name=d.name,
            scan_x=ox,
            scan_y=oy,
            chart_x=d.chart_x,
            chart_y=d.chart_y,
            score=d.score,
        ))
    H = _compute_homography(mapped)
    aligned = warp_scan_to_chart(
        scan, H, _mp_gt["chart_width"], _mp_gt["chart_height"],
    )
    ssim_scores = validate_alignment(aligned, _mp_chart_bgr, _mp_gt["corners"])
    if _mp_save_aligned:
        cv2.imwrite(str(_mp_out_dir / scan_path.name), aligned)
    return (
        scan_path.name,
        ssim_scores,
        sum(1 for d in mapped if d.score > 0),
        best_k,
    )


def align_all_scans(save: bool = True, max_workers: int | None = None) -> dict[str, dict]:
    gt = _load_ground_truth()
    chart = cv2.imread(str(CHART_PATH))
    if chart is None:
        raise FileNotFoundError(CHART_PATH)
    chart_gray = cv2.cvtColor(chart, cv2.COLOR_BGR2GRAY)

    if save:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    scan_paths = sorted(SCANS_DIR.glob("scan*.png"))
    if not scan_paths:
        return {}

    n_workers = max(1, max_workers if max_workers is not None else max_cpu_workers())
    chart_abs = str(CHART_PATH.resolve())
    gt_abs = str(GROUND_TRUTH_PATH.resolve())
    out_abs = str(OUTPUT_DIR.resolve())

    if n_workers <= 1:
        results: dict[str, dict] = {}
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

    phase1_tasks = [
        (str(p.resolve()), k)
        for p in scan_paths
        for k in range(4)
    ]
    ctx = get_context("spawn")
    results: dict[str, dict] = {}
    with ProcessPoolExecutor(
        max_workers=n_workers,
        mp_context=ctx,
        initializer=_mp_align_state_init,
        initargs=(chart_abs, gt_abs, out_abs, save),
    ) as pool:
        phase1_rows = list(pool.map(_mp_align_phase1_orient_task, phase1_tasks))

    by_name: dict[str, list[tuple[int, float, list[CornerDetection]]]] = {}
    for scan_name, rot_k, score, dets in phase1_rows:
        by_name.setdefault(scan_name, []).append((rot_k, score, dets))

    name_to_abs = {p.name: str(p.resolve()) for p in scan_paths}

    def _read_scan_gray(path_abs: str) -> np.ndarray:
        img = cv2.imread(path_abs)
        if img is None:
            raise FileNotFoundError(path_abs)
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    phase2_tasks: list[tuple[str, int, list[CornerDetection]]] = []
    for p in scan_paths:
        name = p.name
        cands = by_name[name]
        best_k, best_score, best_dets = max(cands, key=lambda x: x[1])
        if best_score < 0:
            scan_gray = _read_scan_gray(name_to_abs[name])
            best_dets = detect_corners_in_scan(
                scan_gray, chart_gray, gt["corners"], MATCH_THRESHOLD,
            )
            best_k = 0
        phase2_tasks.append((name_to_abs[name], best_k, best_dets))

    with ProcessPoolExecutor(
        max_workers=n_workers,
        mp_context=ctx,
        initializer=_mp_align_state_init,
        initargs=(chart_abs, gt_abs, out_abs, save),
    ) as pool:
        phase2_rows = list(pool.map(_mp_align_phase2_warp_task, phase2_tasks))

    scan_order = {p.name: i for i, p in enumerate(scan_paths)}
    phase2_rows.sort(key=lambda row: scan_order[row[0]])

    for name, ssim_scores, corners_n, orientation_k in phase2_rows:
        print(f"Aligning {name}...")
        if save:
            print(f"  Saved to {OUTPUT_DIR.resolve() / name}")
        results[name] = {
            "ssim": ssim_scores,
            "corners_detected": corners_n,
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
