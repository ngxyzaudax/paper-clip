import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import cv2
import numpy as np


GROUND_TRUTH_PATH = Path(__file__).parent / "ground_truth.json"
ALIGNED_DIR = Path(__file__).parent / "output" / "aligned"
MODELS_DIR = Path(__file__).parent / "output" / "models"
METRICS_DIR = Path(__file__).parent / "output" / "metrics"
DATASET_DIR = Path(__file__).parent / "output" / "dataset"

FIXED_INPUT_SIZE = 32


def _lazy_tf():
    import tensorflow as tf
    return tf


def _load_ground_truth() -> dict:
    return json.loads(GROUND_TRUTH_PATH.read_text())


def _load_model(tf, cell_size: int) -> "tf.keras.Model":
    model_path = MODELS_DIR / f"band_{cell_size}px.keras"
    if not model_path.exists():
        raise FileNotFoundError(f"No model for {cell_size}px at {model_path}")
    return tf.keras.models.load_model(str(model_path))


def _crop_and_predict(
    tf,
    model: "tf.keras.Model",
    aligned: np.ndarray,
    dots: list[dict],
    band_idx: int,
    cell_size: int,
) -> tuple[list[int], list[int]]:
    true_labels = []
    pred_labels = []
    batch_crops = []
    batch_true = []

    h, w = aligned.shape[:2]
    for dot in dots:
        if dot["band_idx"] != band_idx:
            continue
        x, y = dot["cell_x"], dot["cell_y"]
        if x < 0 or y < 0 or y + cell_size > h or x + cell_size > w:
            continue
        crop = aligned[y : y + cell_size, x : x + cell_size]
        if crop.mean() < 30 or crop.std() < 3.0:
            continue
        rgb = crop[:, :, ::-1]
        resized = cv2.resize(rgb, (FIXED_INPUT_SIZE, FIXED_INPUT_SIZE), interpolation=cv2.INTER_AREA)
        batch_crops.append(resized.astype(np.float32))
        batch_true.append(dot["color_idx"])

    if not batch_crops:
        return [], []

    batch = np.stack(batch_crops)
    predictions = model.predict(batch, verbose=0)
    pred_classes = np.argmax(predictions, axis=1)

    return batch_true, pred_classes.tolist()


def evaluate_per_scan(
    cell_sizes: list[int] | None = None,
) -> dict:
    tf = _lazy_tf()
    gt = _load_ground_truth()
    dots = gt["dots"]
    bands = gt["bands"]
    num_colors = len(gt["colors"])

    if cell_sizes is None:
        cell_sizes = sorted(
            cs for cs in set(b["cell_size"] for b in bands)
            if (MODELS_DIR / f"band_{cs}px.keras").exists()
        )

    models = {}
    for cs in cell_sizes:
        models[cs] = _load_model(tf, cs)
        print(f"Loaded model for {cs}px")

    band_by_size = {}
    for bi, b in enumerate(bands):
        if b["cell_size"] in models:
            band_by_size.setdefault(b["cell_size"], []).append(bi)

    results: dict[str, Any] = {"per_scan": {}, "per_band": {}, "per_color": {}, "overall": {}}

    all_true: list[int] = []
    all_pred: list[int] = []
    per_cs_true: dict[int, list[int]] = defaultdict(list)
    per_cs_pred: dict[int, list[int]] = defaultdict(list)
    scan_paths = sorted(ALIGNED_DIR.glob("scan*.png"))

    for scan_path in scan_paths:
        scan_name = scan_path.name
        print(f"\nEvaluating {scan_name}...")
        aligned = cv2.imread(str(scan_path))
        if aligned is None:
            continue

        scan_true: list[int] = []
        scan_pred: list[int] = []

        for cs in cell_sizes:
            model = models[cs]
            for bi in band_by_size.get(cs, []):
                true, pred = _crop_and_predict(tf, model, aligned, dots, bi, cs)
                scan_true.extend(true)
                scan_pred.extend(pred)
                per_cs_true[cs].extend(true)
                per_cs_pred[cs].extend(pred)

        if scan_true:
            correct = sum(t == p for t, p in zip(scan_true, scan_pred))
            acc = correct / len(scan_true)
            results["per_scan"][scan_name] = {
                "accuracy": acc,
                "total": len(scan_true),
                "correct": correct,
            }
            print(f"  {scan_name}: {acc:.4f} ({correct}/{len(scan_true)})")

        all_true.extend(scan_true)
        all_pred.extend(scan_pred)

    if all_true:
        overall_acc = sum(t == p for t, p in zip(all_true, all_pred)) / len(all_true)
        results["overall"] = {
            "accuracy": overall_acc,
            "total": len(all_true),
        }

    for cs in cell_sizes:
        t, p = per_cs_true[cs], per_cs_pred[cs]
        if t:
            correct = sum(a == b for a, b in zip(t, p))
            results["per_band"][str(cs)] = {
                "accuracy": correct / len(t),
                "count": len(t),
                "correct": correct,
            }
    _compute_per_color_accuracy(results, all_true, all_pred, num_colors, gt["colors"])
    _save_confusion_matrix(all_true, all_pred, num_colors)

    return results


def _compute_per_color_accuracy(
    results: dict,
    all_true: list[int],
    all_pred: list[int],
    num_colors: int,
    colors: list[list[int]],
) -> None:
    per_color = {}
    for c in range(num_colors):
        indices = [i for i, t in enumerate(all_true) if t == c]
        if not indices:
            continue
        correct = sum(1 for i in indices if all_pred[i] == c)
        per_color[c] = {
            "rgb": colors[c],
            "accuracy": correct / len(indices),
            "total": len(indices),
            "correct": correct,
        }
    results["per_color"] = per_color


def _save_confusion_matrix(
    all_true: list[int],
    all_pred: list[int],
    num_colors: int,
) -> None:
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    cm = np.zeros((num_colors, num_colors), dtype=np.int32)
    for t, p in zip(all_true, all_pred):
        if 0 <= t < num_colors and 0 <= p < num_colors:
            cm[t, p] += 1

    np.savetxt(str(METRICS_DIR / "confusion_matrix.csv"), cm, delimiter=",", fmt="%d")

    cell_size = 20
    img_size = num_colors * cell_size
    cm_img = np.zeros((img_size, img_size, 3), dtype=np.uint8)
    cm_norm = cm.astype(np.float32)
    row_sums = cm_norm.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1
    cm_norm = cm_norm / row_sums

    for i in range(num_colors):
        for j in range(num_colors):
            val = int(cm_norm[i, j] * 255)
            color = (val, val, val) if i != j else (0, val, 0)
            y1, y2 = i * cell_size, (i + 1) * cell_size
            x1, x2 = j * cell_size, (j + 1) * cell_size
            cm_img[y1:y2, x1:x2] = color

    scale = 4
    cm_img = cv2.resize(cm_img, (img_size * scale, img_size * scale), interpolation=cv2.INTER_NEAREST)
    cv2.imwrite(str(METRICS_DIR / "confusion_matrix.png"), cm_img)


if __name__ == "__main__":
    results = evaluate_per_scan()

    print("\n" + "=" * 60)
    print("EVALUATION RESULTS")
    print("=" * 60)

    if results["overall"]:
        print(f"\nOverall accuracy: {results['overall']['accuracy']:.4f} ({results['overall']['total']} samples)")

    print("\nPer-scan accuracy:")
    for name, info in sorted(results["per_scan"].items()):
        print(f"  {name}: {info['accuracy']:.4f} ({info['correct']}/{info['total']})")

    print("\nPer-color accuracy:")
    sorted_colors = sorted(results["per_color"].items(), key=lambda x: x[1]["accuracy"])
    for c, info in sorted_colors[:5]:
        print(f"  Color {c} (RGB={info['rgb']}): {info['accuracy']:.4f} ({info['correct']}/{info['total']})")
    print("  ...")
    for c, info in sorted_colors[-5:]:
        print(f"  Color {c} (RGB={info['rgb']}): {info['accuracy']:.4f} ({info['correct']}/{info['total']})")

    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    (METRICS_DIR / "evaluation_results.json").write_text(json.dumps(results, indent=2))
    print(f"\nFull results saved to {METRICS_DIR / 'evaluation_results.json'}")
