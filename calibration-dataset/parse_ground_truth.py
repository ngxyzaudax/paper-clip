import json
from pathlib import Path

import cv2
import numpy as np


CHART_PATH = Path(__file__).parent / "calibration_chart.png"
OUTPUT_PATH = Path(__file__).parent / "ground_truth.json"

APRILTAG_CENTERS = {
    "tl": [235, 235],
    "tr": [9686, 235],
    "bl": [235, 13796],
    "br": [9686, 13796],
}

MIN_BLOB_GAP = 2
MIN_NON_WHITE_PX = 10
BAND_MERGE_GAP = 30


def _load_chart() -> np.ndarray:
    chart = cv2.imread(str(CHART_PATH))
    if chart is None:
        raise FileNotFoundError(f"Cannot read {CHART_PATH}")
    return chart


def _non_white_mask_row(row: np.ndarray) -> np.ndarray:
    return np.any(row != [255, 255, 255], axis=1)


def _find_blob_starts(mask: np.ndarray) -> list[int]:
    indices = np.where(mask)[0]
    if len(indices) == 0:
        return []
    diffs = np.diff(indices)
    gaps = np.where(diffs > MIN_BLOB_GAP)[0]
    return [int(indices[0])] + [int(indices[g + 1]) for g in gaps]


def _find_content_rows(chart: np.ndarray, x_margin: int = 300) -> list[int]:
    h, w = chart.shape[:2]
    content_rows = []
    for y in range(h):
        row = chart[y, x_margin : w - x_margin]
        if np.sum(_non_white_mask_row(row)) > MIN_NON_WHITE_PX:
            content_rows.append(y)
    return content_rows


def _group_into_bands(
    content_rows: list[int],
) -> list[tuple[int, int]]:
    if not content_rows:
        return []
    bands = []
    band_start = content_rows[0]
    prev = content_rows[0]
    for y in content_rows[1:]:
        if y - prev > BAND_MERGE_GAP:
            bands.append((band_start, prev))
            band_start = y
        prev = y
    bands.append((band_start, prev))
    return bands


def _measure_cell_size_at_row(chart: np.ndarray, y: int) -> tuple[int, int, list[int]]:
    row = chart[y, :]
    mask = _non_white_mask_row(row)
    blob_starts = _find_blob_starts(mask)
    if len(blob_starts) < 3:
        return 0, len(blob_starts), blob_starts
    spacings = np.diff(blob_starts)
    cell_size = int(np.median(spacings))
    return cell_size, len(blob_starts), blob_starts


def _split_density_bands(
    chart: np.ndarray, y_start: int, y_end: int,
) -> list[dict]:
    bands = []
    current_cell = 0
    current_start = y_start
    current_cols = 0
    current_margin_x = 0

    for y in range(y_start, y_end + 1):
        cell_size, num_cols, blob_starts = _measure_cell_size_at_row(chart, y)
        if cell_size == 0:
            continue
        if cell_size != current_cell:
            if current_cell > 0:
                row_count = _count_dot_rows(
                    chart, current_start, y - 1, current_cell, current_margin_x, current_cols,
                )
                bands.append({
                    "cell_size": current_cell,
                    "y_start": current_start,
                    "y_end": y - 1,
                    "num_rows": row_count,
                    "num_cols": current_cols,
                    "margin_x": current_margin_x,
                })
            current_cell = cell_size
            current_start = y
            current_cols = num_cols
            current_margin_x = int(blob_starts[0]) if blob_starts else 0
    if current_cell > 0:
        row_count = _count_dot_rows(
            chart, current_start, y_end, current_cell, current_margin_x, current_cols,
        )
        bands.append({
            "cell_size": current_cell,
            "y_start": current_start,
            "y_end": y_end,
            "num_rows": row_count,
            "num_cols": current_cols,
            "margin_x": current_margin_x,
        })
    return bands


def _count_dot_rows(
    chart: np.ndarray, y_start: int, y_end: int, cell_size: int, margin_x: int, num_cols: int,
) -> int:
    count = 0
    y = y_start
    dot_region_x_end = margin_x + num_cols * cell_size
    while y <= y_end:
        row_slice = chart[y, margin_x:dot_region_x_end]
        mask = _non_white_mask_row(row_slice)
        blobs = _find_blob_starts(mask)
        if len(blobs) >= num_cols // 2:
            count += 1
            y += cell_size
        else:
            y += 1
    return count


def _extract_cell_color(
    chart: np.ndarray, cell_x: int, cell_y: int, cell_size: int,
) -> list[int] | None:
    h, w = chart.shape[:2]
    y2 = min(cell_y + cell_size, h)
    x2 = min(cell_x + cell_size, w)
    cell = chart[cell_y:y2, cell_x:x2]
    if cell.size == 0:
        return None
    mask = np.any(cell != [255, 255, 255], axis=2)
    colored = cell[mask]
    if len(colored) == 0:
        return None
    unique, counts = np.unique(colored.reshape(-1, 3), axis=0, return_counts=True)
    dominant_bgr = unique[np.argmax(counts)]
    return [int(dominant_bgr[2]), int(dominant_bgr[1]), int(dominant_bgr[0])]


def _extract_dots_from_bands(
    chart: np.ndarray,
    bands: list[dict],
) -> tuple[list[dict], list[list[int]]]:
    dots = []
    color_set: dict[tuple[int, int, int], int] = {}
    colors: list[list[int]] = []

    for band_idx, band in enumerate(bands):
        cell_size = band["cell_size"]
        margin_x = band["margin_x"]

        for row in range(band["num_rows"]):
            dot_y = band["y_start"] + row * cell_size
            if dot_y >= chart.shape[0]:
                break
            for col in range(band["num_cols"]):
                dot_x = margin_x + col * cell_size
                if dot_x >= chart.shape[1]:
                    break

                rgb = _extract_cell_color(chart, dot_x, dot_y, cell_size)
                if rgb is None:
                    continue

                rgb_key = tuple(rgb)
                cx = dot_x + cell_size // 2
                cy = dot_y + cell_size // 2

                if rgb_key not in color_set:
                    color_set[rgb_key] = len(colors)
                    colors.append(rgb)

                dots.append({
                    "band_idx": band_idx,
                    "row": row,
                    "col": col,
                    "cx": cx,
                    "cy": cy,
                    "cell_x": dot_x,
                    "cell_y": dot_y,
                    "cell_size": cell_size,
                    "color_idx": color_set[rgb_key],
                    "rgb": rgb,
                })

    return dots, colors


MIN_CELL_PX = 10
MAX_CELL_PX = 30
MIN_BAND_ROWS = 4


def _filter_density_bands(bands: list[dict]) -> list[dict]:
    return [
        b for b in bands
        if MIN_CELL_PX <= b["cell_size"] <= MAX_CELL_PX and b["num_rows"] >= MIN_BAND_ROWS
    ]


def parse_ground_truth() -> dict:
    chart = _load_chart()
    h, w = chart.shape[:2]
    print(f"Chart loaded: {w}x{h}")

    content_rows = _find_content_rows(chart)
    raw_regions = _group_into_bands(content_rows)
    print(f"Found {len(raw_regions)} content regions")

    all_density = []
    for start, end in raw_regions:
        all_density.extend(_split_density_bands(chart, start, end))

    density_bands = _filter_density_bands(all_density)
    print(f"Found {len(density_bands)} density bands (filtered {len(all_density) - len(density_bands)} non-density regions):")
    for b in density_bands:
        print(f"  cell={b['cell_size']}px: {b['num_rows']} rows x {b['num_cols']} cols, y={b['y_start']}..{b['y_end']}")

    dots, colors = _extract_dots_from_bands(chart, density_bands)
    expected_total = sum(b["num_rows"] * b["num_cols"] for b in density_bands)
    print(f"Extracted {len(dots)} dots (expected {expected_total}), {len(colors)} unique colors")

    result = {
        "chart_width": w,
        "chart_height": h,
        "corners": APRILTAG_CENTERS,
        "bands": density_bands,
        "dots": dots,
        "colors": colors,
    }
    return result


def save_ground_truth() -> Path:
    result = parse_ground_truth()
    OUTPUT_PATH.write_text(json.dumps(result, indent=2))
    print(f"Saved ground truth to {OUTPUT_PATH} ({len(result['dots'])} dots, {len(result['colors'])} colors)")
    return OUTPUT_PATH


if __name__ == "__main__":
    save_ground_truth()
