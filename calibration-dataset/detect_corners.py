import json
import logging
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from multiprocessing import get_context
from pathlib import Path

import cv2
import numpy as np

from orientation import map_cw_rotated_to_original
from pool_util import max_cpu_workers

log = logging.getLogger(__name__)


GROUND_TRUTH_PATH = Path(__file__).parent / "ground_truth.json"
CHART_PATH = Path(__file__).parent / "calibration_chart.png"
SCANS_DIR = Path(__file__).parent / "scans"

TEMPLATE_HALF = 200
MATCH_THRESHOLD = 0.35

_mp_chart_gray: np.ndarray | None = None
_mp_corners: dict[str, list[int]] | None = None


@dataclass(frozen=True)
class CornerDetection:
    name: str
    scan_x: float
    scan_y: float
    chart_x: float
    chart_y: float
    score: float


def _load_ground_truth() -> dict:
    return json.loads(GROUND_TRUTH_PATH.read_text())


def _load_gray(path: Path) -> np.ndarray:
    img = cv2.imread(str(path))
    if img is None:
        raise FileNotFoundError(f"Cannot read {path}")
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


def _crop_template(
    chart_gray: np.ndarray, cx: int, cy: int, half: int,
) -> tuple[np.ndarray, int, int]:
    h, w = chart_gray.shape
    y1 = max(0, cy - half)
    y2 = min(h, cy + half)
    x1 = max(0, cx - half)
    x2 = min(w, cx + half)
    offset_x = cx - x1
    offset_y = cy - y1
    return chart_gray[y1:y2, x1:x2], offset_x, offset_y


SEARCH_MARGIN = 500


def _search_region(
    name: str, scan_h: int, scan_w: int, chart_h: int, chart_w: int,
) -> tuple[int, int, int, int]:
    max_shift_x = scan_w - chart_w + SEARCH_MARGIN
    max_shift_y = scan_h - chart_h + SEARCH_MARGIN
    mid_x = scan_w // 2
    mid_y = scan_h // 2
    regions = {
        "tl": (0, 0, mid_x + max_shift_x, mid_y + max_shift_y),
        "tr": (mid_x - max_shift_x, 0, scan_w, mid_y + max_shift_y),
        "bl": (0, mid_y - max_shift_y, mid_x + max_shift_x, scan_h),
        "br": (mid_x - max_shift_x, mid_y - max_shift_y, scan_w, scan_h),
    }
    x1, y1, x2, y2 = regions[name]
    return max(0, x1), max(0, y1), min(scan_w, x2), min(scan_h, y2)


def _match_template_in_region(
    scan_gray: np.ndarray,
    template: np.ndarray,
    x1: int, y1: int, x2: int, y2: int,
    threshold: float,
) -> tuple[float, float, float] | None:
    th, tw = template.shape[:2]
    region = scan_gray[y1:y2, x1:x2]
    if region.shape[0] < th or region.shape[1] < tw:
        return None
    result = cv2.matchTemplate(region, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    if max_val < threshold:
        return None
    return float(max_loc[0] + x1), float(max_loc[1] + y1), float(max_val)


def _detect_single_corner(
    name: str,
    cx: int,
    cy: int,
    scan_gray: np.ndarray,
    chart_gray: np.ndarray,
    threshold: float,
) -> CornerDetection | None:
    sh, sw = scan_gray.shape
    ch, cw = chart_gray.shape
    x1, y1, x2, y2 = _search_region(name, sh, sw, ch, cw)

    for half in [TEMPLATE_HALF, TEMPLATE_HALF + 100, TEMPLATE_HALF - 50]:
        if half <= 0:
            continue
        template, off_x, off_y = _crop_template(chart_gray, cx, cy, half)
        match = _match_template_in_region(scan_gray, template, x1, y1, x2, y2, threshold)
        if match is not None:
            mx, my, score = match
            return CornerDetection(
                name=name, scan_x=mx + off_x, scan_y=my + off_y,
                chart_x=float(cx), chart_y=float(cy), score=score,
            )
    return None


def _infer_missing_corners(
    detections: list[CornerDetection],
    corners: dict[str, list[int]],
) -> list[CornerDetection]:
    detected = {d.name: d for d in detections}
    all_names = ["tl", "tr", "bl", "br"]
    missing = [n for n in all_names if n not in detected]
    if len(missing) == 0 or len(detected) < 2:
        return detections

    src = np.float32([[detected[n].scan_x, detected[n].scan_y] for n in detected])
    dst = np.float32([[detected[n].chart_x, detected[n].chart_y] for n in detected])

    if len(detected) >= 4:
        H, _ = cv2.findHomography(dst, src, 0)
    elif len(detected) == 3:
        M = cv2.getAffineTransform(dst[:3], src[:3])
        H = np.vstack([M, [0, 0, 1]])
    elif len(detected) == 2:
        H = _estimate_transform_from_two(detected, corners)
    else:
        H = None

    if H is None:
        return detections

    result = list(detections)
    for name in missing:
        cx, cy = corners[name]
        chart_pt = np.float32([[cx, cy]]).reshape(-1, 1, 2)
        if H.shape[0] == 3:
            scan_pt = cv2.perspectiveTransform(chart_pt, H).reshape(2)
        else:
            scan_pt = cv2.transform(chart_pt, H).reshape(2)
        result.append(CornerDetection(
            name=name, scan_x=float(scan_pt[0]), scan_y=float(scan_pt[1]),
            chart_x=float(cx), chart_y=float(cy), score=0.0,
        ))
    return result


def _estimate_transform_from_two(
    detected: dict[str, CornerDetection],
    corners: dict[str, list[int]],
) -> np.ndarray | None:
    names = list(detected.keys())
    d0, d1 = detected[names[0]], detected[names[1]]

    src_vec = np.array([d1.scan_x - d0.scan_x, d1.scan_y - d0.scan_y])
    dst_vec = np.array([d1.chart_x - d0.chart_x, d1.chart_y - d0.chart_y])

    src_len = np.linalg.norm(src_vec)
    dst_len = np.linalg.norm(dst_vec)
    if dst_len < 1e-6:
        return None

    scale = src_len / dst_len
    angle = np.arctan2(src_vec[1], src_vec[0]) - np.arctan2(dst_vec[1], dst_vec[0])
    cos_a, sin_a = np.cos(angle), np.sin(angle)

    R = scale * np.array([[cos_a, -sin_a], [sin_a, cos_a]])
    t = np.array([d0.scan_x, d0.scan_y]) - R @ np.array([d0.chart_x, d0.chart_y])

    H = np.eye(3, dtype=np.float64)
    H[:2, :2] = R
    H[:2, 2] = t
    return H


def detect_corners_in_scan(
    scan_gray: np.ndarray,
    chart_gray: np.ndarray,
    corners: dict[str, list[int]],
    threshold: float = MATCH_THRESHOLD,
) -> list[CornerDetection]:
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    scan_clahe = clahe.apply(scan_gray)

    detections = []
    for name, (cx, cy) in corners.items():
        det = _detect_single_corner(name, cx, cy, scan_gray, chart_gray, threshold)
        if det is None:
            det = _detect_single_corner(name, cx, cy, scan_clahe, chart_gray, threshold)
        if det is not None:
            detections.append(det)

    if len(detections) < 4 and len(detections) >= 2:
        detections = _infer_missing_corners(detections, corners)

    return detections


def detect_corners_oriented(
    scan_gray: np.ndarray,
    chart_gray: np.ndarray,
    corners: dict[str, list[int]],
    threshold: float = MATCH_THRESHOLD,
) -> tuple[int, list[CornerDetection]]:
    orig_h, orig_w = scan_gray.shape[:2]
    best_k = 0
    best_score = -1.0
    best_dets: list[CornerDetection] = []

    for k in range(4):
        if k == 0:
            rot = scan_gray
        else:
            rot = scan_gray.copy()
            for _ in range(k):
                rot = cv2.rotate(rot, cv2.ROTATE_90_CLOCKWISE)

        dets = detect_corners_in_scan(rot, chart_gray, corners, threshold)
        measured = [d for d in dets if d.score > 0]
        if not measured:
            continue
        total = sum(d.score for d in measured)
        score = total + 0.01 * len(measured)
        if score > best_score:
            best_score = score
            best_k = k
            best_dets = dets

    if not best_dets:
        best_k = 0
        best_dets = detect_corners_in_scan(scan_gray, chart_gray, corners, threshold)

    mapped: list[CornerDetection] = []
    for d in best_dets:
        ox, oy = map_cw_rotated_to_original(
            d.scan_x, d.scan_y, best_k, orig_w, orig_h,
        )
        mapped.append(CornerDetection(
            name=d.name,
            scan_x=ox, scan_y=oy,
            chart_x=d.chart_x, chart_y=d.chart_y,
            score=d.score,
        ))

    if best_k != 0:
        log.info("Selected orientation: %d clockwise 90-degree steps", best_k)

    return best_k, mapped


def _mp_detect_state_init(chart_abs: str, gt_abs: str) -> None:
    global _mp_chart_gray, _mp_corners
    cv2.setNumThreads(1)
    chart_bgr = cv2.imread(chart_abs)
    if chart_bgr is None:
        raise FileNotFoundError(chart_abs)
    _mp_chart_gray = cv2.cvtColor(chart_bgr, cv2.COLOR_BGR2GRAY)
    _mp_corners = json.loads(Path(gt_abs).read_text())["corners"]


def _mp_detect_one_task(path_and_threshold: tuple[str, float]) -> tuple[str, list[CornerDetection]]:
    path_str, threshold = path_and_threshold
    assert _mp_chart_gray is not None and _mp_corners is not None
    scan_gray = _load_gray(Path(path_str))
    dets = detect_corners_in_scan(scan_gray, _mp_chart_gray, _mp_corners, threshold)
    return Path(path_str).name, dets


def detect_all_scans(
    threshold: float = MATCH_THRESHOLD,
    max_workers: int | None = None,
) -> dict[str, list[CornerDetection]]:
    scan_paths = sorted(SCANS_DIR.glob("scan*.png"))
    if not scan_paths:
        return {}

    chart_abs = str(CHART_PATH.resolve())
    gt_abs = str(GROUND_TRUTH_PATH.resolve())
    n_workers = max(1, max_workers if max_workers is not None else max_cpu_workers())
    items = [(str(p.resolve()), threshold) for p in scan_paths]

    results: dict[str, list[CornerDetection]] = {}
    ctx = get_context("spawn")
    with ProcessPoolExecutor(
        max_workers=n_workers,
        mp_context=ctx,
        initializer=_mp_detect_state_init,
        initargs=(chart_abs, gt_abs),
    ) as pool:
        for name, detections in pool.map(_mp_detect_one_task, items):
            results[name] = detections
            detected_names = [d.name for d in detections]
            scores = [f"{d.score:.3f}" for d in detections]
            print(f"{name}: {len(detections)}/4 corners detected {detected_names} scores={scores}")

    return results


def compute_reprojection_error(detections: list[CornerDetection]) -> float | None:
    measured = [d for d in detections if d.score > 0]
    if len(measured) < 2:
        return None
    src = np.float32([[d.scan_x, d.scan_y] for d in measured])
    dst = np.float32([[d.chart_x, d.chart_y] for d in measured])
    if len(measured) >= 4:
        H, _ = cv2.findHomography(src, dst, 0)
    elif len(measured) == 3:
        M = cv2.getAffineTransform(src[:3], dst[:3])
        H = np.vstack([M, [0, 0, 1]])
    else:
        return 0.0
    if H is None:
        return None
    projected = cv2.perspectiveTransform(src.reshape(-1, 1, 2), H).reshape(-1, 2)
    errors = np.sqrt(np.sum((projected - dst) ** 2, axis=1))
    return float(np.mean(errors))


def _count_measured(detections: list[CornerDetection]) -> int:
    return sum(1 for d in detections if d.score > 0)


if __name__ == "__main__":
    results = detect_all_scans()
    print("\n=== Summary ===")
    total_ok = 0
    for scan_name, detections in results.items():
        measured = _count_measured(detections)
        inferred = len(detections) - measured
        err = compute_reprojection_error(detections)
        err_str = f"{err:.2f}px" if err is not None else "N/A"
        status = "OK" if measured >= 2 else "FAIL"
        if measured >= 2:
            total_ok += 1
        print(f"  {scan_name}: {measured} measured + {inferred} inferred, reproj_err={err_str} [{status}]")
    print(f"\nReliable: {total_ok}/{len(results)} scans")
