import json
from collections import Counter
from pathlib import Path

import cv2
import numpy as np


GROUND_TRUTH_PATH = Path(__file__).parent / "ground_truth.json"
ALIGNED_DIR = Path(__file__).parent / "output" / "aligned"
SAMPLES_DIR = Path(__file__).parent / "output" / "samples"

MIN_CROP_BRIGHTNESS = 30
MIN_CROP_STD = 3.0


def _load_ground_truth() -> dict:
    return json.loads(GROUND_TRUTH_PATH.read_text())


def _crop_cell(
    image: np.ndarray, x: int, y: int, size: int,
) -> np.ndarray | None:
    h, w = image.shape[:2]
    if x < 0 or y < 0 or y + size > h or x + size > w:
        return None
    return image[y : y + size, x : x + size].copy()


def _is_valid_crop(crop: np.ndarray) -> bool:
    if float(crop.mean()) < MIN_CROP_BRIGHTNESS:
        return False
    if float(crop.std()) < MIN_CROP_STD:
        return False
    return True


def extract_dots_from_aligned(
    aligned: np.ndarray,
    dots: list[dict],
) -> tuple[list[np.ndarray], list[int], list[int]]:
    crops = []
    labels = []
    dot_indices = []

    for i, dot in enumerate(dots):
        crop = _crop_cell(aligned, dot["cell_x"], dot["cell_y"], dot["cell_size"])
        if crop is None:
            continue
        if not _is_valid_crop(crop):
            continue
        crops.append(crop)
        labels.append(dot["color_idx"])
        dot_indices.append(i)

    return crops, labels, dot_indices


def extraction_stats(
    dots: list[dict],
    labels: list[int],
    dot_indices: list[int],
    bands: list[dict],
) -> dict:
    total = len(dots)
    extracted = len(labels)
    rate = extracted / total if total > 0 else 0.0

    extracted_set = set(dot_indices)
    per_band = {}
    for bi, band in enumerate(bands):
        band_total = sum(1 for d in dots if d["band_idx"] == bi)
        band_extracted = sum(1 for i in dot_indices if dots[i]["band_idx"] == bi)
        per_band[band["cell_size"]] = {
            "total": band_total,
            "extracted": band_extracted,
            "rate": band_extracted / band_total if band_total > 0 else 0.0,
        }

    return {
        "total": total,
        "extracted": extracted,
        "rate": rate,
        "per_band": per_band,
    }


def _save_montage(
    crops: list[np.ndarray],
    labels: list[int],
    cell_size: int,
    num_colors: int,
    output_path: Path,
    samples_per_class: int = 4,
) -> None:
    by_class: dict[int, list[np.ndarray]] = {}
    for crop, label in zip(crops, labels):
        if crop.shape[0] != cell_size or crop.shape[1] != cell_size:
            continue
        by_class.setdefault(label, [])
        if len(by_class[label]) < samples_per_class:
            by_class[label].append(crop)

    scale = max(1, 32 // cell_size)
    tile_size = cell_size * scale
    cols = samples_per_class
    rows = num_colors

    montage = np.full((rows * tile_size, cols * tile_size, 3), 200, dtype=np.uint8)
    for class_idx in range(num_colors):
        samples = by_class.get(class_idx, [])
        for j, crop in enumerate(samples):
            if j >= cols:
                break
            resized = cv2.resize(crop, (tile_size, tile_size), interpolation=cv2.INTER_NEAREST)
            y = class_idx * tile_size
            x = j * tile_size
            montage[y : y + tile_size, x : x + tile_size] = resized

    cv2.imwrite(str(output_path), montage)


def extract_and_report(scan_name: str, gt: dict) -> dict:
    aligned_path = ALIGNED_DIR / scan_name
    aligned = cv2.imread(str(aligned_path))
    if aligned is None:
        raise FileNotFoundError(f"Cannot read {aligned_path}")

    crops, labels, dot_indices = extract_dots_from_aligned(aligned, gt["dots"])
    stats = extraction_stats(gt["dots"], labels, dot_indices, gt["bands"])

    return {
        "crops": crops,
        "labels": labels,
        "dot_indices": dot_indices,
        "stats": stats,
    }


def extract_all_scans(save_samples: bool = True) -> dict[str, dict]:
    gt = _load_ground_truth()
    num_colors = len(gt["colors"])

    if save_samples:
        SAMPLES_DIR.mkdir(parents=True, exist_ok=True)

    results = {}
    for scan_path in sorted(ALIGNED_DIR.glob("scan*.png")):
        scan_name = scan_path.name
        print(f"Extracting from {scan_name}...")
        result = extract_and_report(scan_name, gt)
        stats = result["stats"]
        print(f"  Extracted: {stats['extracted']}/{stats['total']} ({stats['rate']:.1%})")

        low_bands = [
            f"{sz}px({info['rate']:.0%})"
            for sz, info in sorted(stats["per_band"].items())
            if info["rate"] < 0.95
        ]
        if low_bands:
            print(f"  Low extraction: {', '.join(low_bands)}")

        if save_samples:
            for band in gt["bands"]:
                cs = band["cell_size"]
                band_crops = [
                    c for c, idx in zip(result["crops"], result["dot_indices"])
                    if gt["dots"][idx]["cell_size"] == cs
                ]
                band_labels = [
                    l for l, idx in zip(result["labels"], result["dot_indices"])
                    if gt["dots"][idx]["cell_size"] == cs
                ]
                if band_crops:
                    montage_path = SAMPLES_DIR / f"{scan_name.replace('.png', '')}_{cs}px.png"
                    _save_montage(band_crops, band_labels, cs, num_colors, montage_path)

        results[scan_name] = {
            "stats": stats,
            "num_crops": len(result["crops"]),
        }

    return results


if __name__ == "__main__":
    results = extract_all_scans()
    print("\n=== Extraction Summary ===")
    for scan_name, info in results.items():
        rate = info["stats"]["rate"]
        n = info["num_crops"]
        print(f"  {scan_name}: {n} crops ({rate:.1%})")
