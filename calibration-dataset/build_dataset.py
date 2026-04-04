import json
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import numpy as np

from extract_dots import extract_dots_from_aligned


GROUND_TRUTH_PATH = Path(__file__).parent / "ground_truth.json"
ALIGNED_DIR = Path(__file__).parent / "output" / "aligned"
DATASET_DIR = Path(__file__).parent / "output" / "dataset"


def _lazy_tf():
    import tensorflow as tf
    return tf


def _load_ground_truth() -> dict:
    return json.loads(GROUND_TRUTH_PATH.read_text())


def _make_example(tf, crop_rgb: np.ndarray, label: int, scan_idx: int) -> "tf.train.Example":
    return tf.train.Example(features=tf.train.Features(feature={
        "image": tf.train.Feature(bytes_list=tf.train.BytesList(value=[crop_rgb.tobytes()])),
        "label": tf.train.Feature(int64_list=tf.train.Int64List(value=[label])),
        "height": tf.train.Feature(int64_list=tf.train.Int64List(value=[crop_rgb.shape[0]])),
        "width": tf.train.Feature(int64_list=tf.train.Int64List(value=[crop_rgb.shape[1]])),
        "scan_idx": tf.train.Feature(int64_list=tf.train.Int64List(value=[scan_idx])),
    }))


def _write_tfrecord(
    tf,
    crops: list[np.ndarray],
    labels: list[int],
    scan_indices: list[int],
    output_path: Path,
) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tf.io.TFRecordWriter(str(output_path)) as writer:
        for crop, label, scan_idx in zip(crops, labels, scan_indices):
            rgb = crop[:, :, ::-1]
            writer.write(_make_example(tf, rgb, label, scan_idx).SerializeToString())
    return len(labels)


def build_all_datasets() -> dict:
    tf = _lazy_tf()
    gt = _load_ground_truth()
    num_colors = len(gt["colors"])
    dots = gt["dots"]
    bands = gt["bands"]

    DATASET_DIR.mkdir(parents=True, exist_ok=True)

    all_crops: list[np.ndarray] = []
    all_labels: list[int] = []
    all_scan_indices: list[int] = []
    all_cell_sizes: list[int] = []

    scan_paths = sorted(ALIGNED_DIR.glob("scan*.png"))
    for scan_idx, scan_path in enumerate(scan_paths):
        print(f"Loading {scan_path.name}...")
        aligned = cv2.imread(str(scan_path))
        if aligned is None:
            print(f"  SKIP: cannot read")
            continue

        crops, labels, dot_indices = extract_dots_from_aligned(aligned, dots)
        cell_sizes = [dots[i]["cell_size"] for i in dot_indices]

        all_crops.extend(crops)
        all_labels.extend(labels)
        all_scan_indices.extend([scan_idx] * len(crops))
        all_cell_sizes.extend(cell_sizes)
        print(f"  {len(crops)} crops extracted")

    print(f"\nTotal: {len(all_crops)} crops from {len(scan_paths)} scans")

    per_band_crops: dict[int, tuple[list[np.ndarray], list[int], list[int]]] = defaultdict(
        lambda: ([], [], [])
    )
    for crop, label, scan_idx, cs in zip(all_crops, all_labels, all_scan_indices, all_cell_sizes):
        c, l, s = per_band_crops[cs]
        c.append(crop)
        l.append(label)
        s.append(scan_idx)

    stats = {"total": len(all_crops), "per_band": {}, "per_scan": {}}

    for cs in sorted(per_band_crops.keys()):
        crops, labels, scan_indices = per_band_crops[cs]
        out_path = DATASET_DIR / f"band_{cs}px.tfrecord"
        n = _write_tfrecord(tf, crops, labels, scan_indices, out_path)
        class_dist = Counter(labels)
        stats["per_band"][cs] = {
            "count": n,
            "classes": len(class_dist),
            "min_per_class": min(class_dist.values()),
            "max_per_class": max(class_dist.values()),
        }
        print(f"  band_{cs}px.tfrecord: {n} examples, {len(class_dist)} classes")

    combined_path = DATASET_DIR / "all_bands.tfrecord"
    _write_tfrecord(tf, all_crops, all_labels, all_scan_indices, combined_path)
    print(f"  all_bands.tfrecord: {len(all_crops)} examples")

    scan_counts = Counter(all_scan_indices)
    for si, count in sorted(scan_counts.items()):
        stats["per_scan"][si] = count

    class_dist_all = Counter(all_labels)
    stats["class_balance"] = {
        "num_classes": len(class_dist_all),
        "min_per_class": min(class_dist_all.values()),
        "max_per_class": max(class_dist_all.values()),
        "mean_per_class": int(np.mean(list(class_dist_all.values()))),
    }

    stats_path = DATASET_DIR / "dataset_stats.json"
    stats_path.write_text(json.dumps(stats, indent=2))
    print(f"\nDataset stats saved to {stats_path}")
    print(f"Class balance: {stats['class_balance']}")

    return stats


if __name__ == "__main__":
    stats = build_all_datasets()
