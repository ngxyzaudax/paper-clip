import json
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import get_context
from pathlib import Path

import cv2
import numpy as np

from extract_dots import extract_dots_from_aligned
from pool_util import max_cpu_workers


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


_mp_dots: list[dict] | None = None


def _mp_build_extract_init(gt_abs: str) -> None:
    global _mp_dots
    cv2.setNumThreads(1)
    _mp_dots = json.loads(Path(gt_abs).read_text())["dots"]


def _mp_build_extract_one(
    idx_path: tuple[int, str],
) -> tuple[int, list, list, list, list, bool]:
    scan_idx, path_str = idx_path
    assert _mp_dots is not None
    aligned = cv2.imread(path_str)
    if aligned is None:
        return scan_idx, [], [], [], [], False
    crops, labels, dot_indices = extract_dots_from_aligned(aligned, _mp_dots)
    cell_sizes = [_mp_dots[i]["cell_size"] for i in dot_indices]
    scan_indices = [scan_idx] * len(crops)
    return scan_idx, crops, labels, scan_indices, cell_sizes, True


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


def build_all_datasets(max_workers: int | None = None) -> dict:
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
    gt_abs = str(GROUND_TRUTH_PATH.resolve())
    n_workers = max(1, max_workers if max_workers is not None else max_cpu_workers())

    if n_workers <= 1:
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
    else:
        indexed_paths = [(i, str(p.resolve())) for i, p in enumerate(scan_paths)]
        ctx = get_context("spawn")
        with ProcessPoolExecutor(
            max_workers=n_workers,
            mp_context=ctx,
            initializer=_mp_build_extract_init,
            initargs=(gt_abs,),
        ) as pool:
            chunks = list(pool.map(_mp_build_extract_one, indexed_paths))
        chunks.sort(key=lambda c: c[0])
        for scan_idx, crops, labels, scan_indices, cell_sizes, read_ok in chunks:
            name = scan_paths[scan_idx].name
            print(f"Loading {name}...")
            if not read_ok:
                print(f"  SKIP: cannot read")
            else:
                print(f"  {len(crops)} crops extracted")
            all_crops.extend(crops)
            all_labels.extend(labels)
            all_scan_indices.extend(scan_indices)
            all_cell_sizes.extend(cell_sizes)

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
