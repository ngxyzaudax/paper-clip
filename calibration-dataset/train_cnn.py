import json
from pathlib import Path

import numpy as np


DATASET_DIR = Path(__file__).parent / "output" / "dataset"
MODELS_DIR = Path(__file__).parent / "output" / "models"
GROUND_TRUTH_PATH = Path(__file__).parent / "ground_truth.json"

EPOCHS = 40
BATCH_SIZE = 256
FIXED_INPUT_SIZE = 32
VAL_SCAN_IDX = 8


def _lazy_tf():
    import tensorflow as tf
    return tf


def _load_ground_truth() -> dict:
    return json.loads(GROUND_TRUTH_PATH.read_text())


def _parse_tfrecord(tf):
    def parse_fn(serialized):
        features = tf.io.parse_single_example(serialized, {
            "image": tf.io.FixedLenFeature([], tf.string),
            "label": tf.io.FixedLenFeature([], tf.int64),
            "height": tf.io.FixedLenFeature([], tf.int64),
            "width": tf.io.FixedLenFeature([], tf.int64),
            "scan_idx": tf.io.FixedLenFeature([], tf.int64),
        })
        h = tf.cast(features["height"], tf.int32)
        w = tf.cast(features["width"], tf.int32)
        image = tf.io.decode_raw(features["image"], tf.uint8)
        image = tf.reshape(image, (h, w, 3))
        image = tf.cast(image, tf.float32)
        image = tf.image.resize(
            image, (FIXED_INPUT_SIZE, FIXED_INPUT_SIZE), method="area",
        )
        return image, features["label"], features["scan_idx"]
    return parse_fn


def _tfrecord_dataset(tf, tfrecord_path: Path) -> "tf.data.Dataset":
    return (
        tf.data.TFRecordDataset(str(tfrecord_path))
        .map(_parse_tfrecord(tf), num_parallel_calls=tf.data.AUTOTUNE)
    )


def _materialize_band_from_tfrecord(
    tf, tfrecord_path: Path,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    ds = _tfrecord_dataset(tf, tfrecord_path)
    img_chunks: list[np.ndarray] = []
    lbl_chunks: list[np.ndarray] = []
    scan_chunks: list[np.ndarray] = []
    for batch in ds.batch(4096):
        img_chunks.append(batch[0].numpy())
        lbl_chunks.append(batch[1].numpy())
        scan_chunks.append(batch[2].numpy())
    if not img_chunks:
        raise ValueError(f"Empty TFRecord: {tfrecord_path}")
    return (
        np.concatenate(img_chunks, axis=0),
        np.concatenate(lbl_chunks, axis=0),
        np.concatenate(scan_chunks, axis=0),
    )


def _build_model(tf, num_classes: int) -> "tf.keras.Model":
    inputs = tf.keras.Input(shape=(FIXED_INPUT_SIZE, FIXED_INPUT_SIZE, 3))
    x = tf.keras.layers.Rescaling(1.0 / 255.0)(inputs)
    x = tf.keras.layers.Conv2D(32, 3, activation="relu", padding="same")(x)
    x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.MaxPooling2D(2)(x)
    x = tf.keras.layers.Conv2D(64, 3, activation="relu", padding="same")(x)
    x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.MaxPooling2D(2)(x)
    x = tf.keras.layers.Conv2D(128, 3, activation="relu", padding="same")(x)
    x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    x = tf.keras.layers.Dense(128, activation="relu")(x)
    x = tf.keras.layers.Dropout(0.3)(x)
    outputs = tf.keras.layers.Dense(num_classes, activation="softmax")(x)
    return tf.keras.Model(inputs, outputs)


def _augment(tf, image, label):
    image = tf.image.random_brightness(image, 8.0)
    image = tf.image.random_contrast(image, 0.9, 1.1)
    noise = tf.random.normal(tf.shape(image), stddev=3.0)
    image = tf.clip_by_value(image + noise, 0.0, 255.0)
    return image, label


def _make_train_dataset(
    tf,
    x_train: np.ndarray,
    y_train: np.ndarray,
    batch_size: int,
) -> "tf.data.Dataset":
    n = len(y_train)
    if n == 0:
        raise ValueError("train split is empty")
    xt = tf.constant(x_train, dtype=tf.float32)
    yt = tf.constant(y_train, dtype=tf.int64)

    def aug(img, lbl):
        return _augment(tf, img, lbl)

    return (
        tf.data.Dataset.from_tensor_slices((xt, yt))
        .shuffle(n, reshuffle_each_iteration=True)
        .map(aug, num_parallel_calls=tf.data.AUTOTUNE)
        .batch(batch_size)
        .prefetch(tf.data.AUTOTUNE)
    )


def _make_eval_dataset(
    tf, x: np.ndarray, y: np.ndarray, batch_size: int,
) -> "tf.data.Dataset":
    if len(y) == 0:
        raise ValueError("eval split is empty")
    xv = tf.constant(x, dtype=tf.float32)
    yv = tf.constant(y, dtype=tf.int64)
    return (
        tf.data.Dataset.from_tensor_slices((xv, yv))
        .batch(batch_size)
        .prefetch(tf.data.AUTOTUNE)
    )


def train_single_band(
    cell_size: int,
    num_classes: int,
    epochs: int = EPOCHS,
    batch_size: int = BATCH_SIZE,
) -> tuple[Path, dict]:
    tf = _lazy_tf()
    tfrecord_path = DATASET_DIR / f"band_{cell_size}px.tfrecord"
    if not tfrecord_path.exists():
        raise FileNotFoundError(f"TFRecord not found: {tfrecord_path}")

    images, labels, scans = _materialize_band_from_tfrecord(tf, tfrecord_path)
    train_mask = scans != VAL_SCAN_IDX
    val_mask = scans == VAL_SCAN_IDX
    x_train, y_train = images[train_mask], labels[train_mask]
    x_val, y_val = images[val_mask], labels[val_mask]
    train_count, val_count = len(y_train), len(y_val)

    train_ds = _make_train_dataset(tf, x_train, y_train, batch_size)
    val_ds = _make_eval_dataset(tf, x_val, y_val, batch_size)

    model = _build_model(tf, num_classes)
    model.compile(
        optimizer=tf.keras.optimizers.Adam(1e-3),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )

    callbacks = [
        tf.keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=3),
        tf.keras.callbacks.EarlyStopping(
            monitor="val_accuracy", patience=8, restore_best_weights=True,
        ),
    ]

    print(f"\n--- Training band {cell_size}px ({train_count} train, {val_count} val) ---")
    history = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=epochs,
        callbacks=callbacks,
        verbose=2,
    )

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    model_path = MODELS_DIR / f"band_{cell_size}px.keras"
    model.save(str(model_path))

    va = history.history.get("val_accuracy", [])
    result = {
        "cell_size": cell_size,
        "train_count": train_count,
        "val_count": val_count,
        "final_val_accuracy": float(va[-1]) if va else 0.0,
        "best_val_accuracy": float(max(va)) if va else 0.0,
        "model_path": str(model_path),
    }
    print(f"  Final val_accuracy: {result['final_val_accuracy']:.4f}")
    return model_path, result


def train_leave_one_scan_out(
    cell_size: int,
    num_classes: int,
    held_out_scan: int,
    epochs: int = EPOCHS,
    batch_size: int = BATCH_SIZE,
) -> dict:
    tf = _lazy_tf()
    tfrecord_path = DATASET_DIR / f"band_{cell_size}px.tfrecord"
    images, labels, scans = _materialize_band_from_tfrecord(tf, tfrecord_path)

    train_mask = scans != held_out_scan
    test_mask = scans == held_out_scan
    x_train, y_train = images[train_mask], labels[train_mask]
    x_test, y_test = images[test_mask], labels[test_mask]
    train_count, test_count = len(y_train), len(y_test)

    if test_count == 0:
        return {"held_out_scan": held_out_scan, "test_count": 0, "accuracy": 0.0}

    train_ds = _make_train_dataset(tf, x_train, y_train, batch_size)
    test_ds = _make_eval_dataset(tf, x_test, y_test, batch_size)

    model = _build_model(tf, num_classes)
    model.compile(
        optimizer=tf.keras.optimizers.Adam(1e-3),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )

    print(
        f"\n--- LOSO: band {cell_size}px, held-out scan {held_out_scan} "
        f"({train_count} train, {test_count} test) ---",
    )
    model.fit(train_ds, epochs=epochs, verbose=0)
    _, accuracy = model.evaluate(test_ds, verbose=0)

    return {
        "held_out_scan": held_out_scan,
        "train_count": train_count,
        "test_count": test_count,
        "accuracy": float(accuracy),
    }


def train_all_bands(
    band_sizes: list[int] | None = None,
    epochs: int = EPOCHS,
) -> dict:
    gt = _load_ground_truth()
    num_classes = len(gt["colors"])

    if band_sizes is None:
        band_sizes = sorted(set(b["cell_size"] for b in gt["bands"]))

    results = {}
    for cs in band_sizes:
        _, result = train_single_band(cs, num_classes, epochs=epochs)
        results[cs] = result

    summary_path = MODELS_DIR / "training_summary.json"
    summary_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"\nTraining summary saved to {summary_path}")
    return results


def _parse_cli() -> tuple[list[int] | None, int]:
    import sys
    argv = list(sys.argv[1:])
    epochs = EPOCHS
    sizes: list[int] | None = None
    pos: list[str] = []
    i = 0
    while i < len(argv):
        if argv[i] == "--epochs" and i + 1 < len(argv):
            epochs = int(argv[i + 1])
            i += 2
        else:
            pos.append(argv[i])
            i += 1
    if pos:
        sizes = [int(s) for s in pos]
    return sizes, epochs


if __name__ == "__main__":
    band_sizes, ep = _parse_cli()
    results = train_all_bands(band_sizes=band_sizes, epochs=ep)
    print("\n=== Training Results ===")
    for cs, r in sorted(results.items()):
        print(
            f"  {cs}px: val_acc={r['final_val_accuracy']:.4f} "
            f"(best={r['best_val_accuracy']:.4f})",
        )
