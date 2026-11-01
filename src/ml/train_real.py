import os
from pathlib import Path

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")

import numpy as np
import tensorflow as tf

from ml.network import CELL_PX, build_cell_decoder
from ml.real_batch import RealPage, prepare_page, sample_real_batch
from ml.scan_grid import PageExample
from ml.store import default_model_path
from ml.train import _train_step


def train_on_pages(
    pages: list[PageExample],
    steps: int = 1000,
    batch_size: int = 8,
    output_path: Path | None = None,
    seed: int = 7,
) -> tuple[Path, float]:
    prepared = [prepare_page(page.image, page.labels) for page in pages]
    rng = np.random.default_rng(seed)
    tf.random.set_seed(seed)
    model = build_cell_decoder()
    optimizer = tf.keras.optimizers.Adam(1e-3)
    accuracy = 0.0
    for step in range(steps):
        images, labels, offsets = sample_real_batch(prepared, batch_size, rng)
        loss, accuracy = _train_step(model, optimizer, images, labels, offsets)
        if step % 50 == 0 or step + 1 == steps:
            print(f"step {step + 1}/{steps} loss {float(loss):.4f} accuracy {float(accuracy):.3f}", flush=True)
    accuracy = _held_out_accuracy(model, prepared, rng)
    scored = [_page_accuracy(model, page) for page in prepared]
    print(f"held-out accuracy {accuracy:.3f} page accuracy {' '.join(f'{item:.3f}' for item in scored)}", flush=True)
    destination = output_path or default_model_path()
    destination.parent.mkdir(parents=True, exist_ok=True)
    model.save(str(destination))
    return destination, accuracy


def _held_out_accuracy(model: tf.keras.Model, pages: list[RealPage], rng: np.random.Generator) -> float:
    images, labels, _offsets = sample_real_batch(pages, 16, rng, held=True)
    logits, _predicted = model(tf.constant(images), training=False)
    matches = tf.equal(tf.argmax(logits, axis=-1, output_type=tf.int32), tf.constant(labels))
    return float(tf.reduce_mean(tf.cast(matches, tf.float32)))


def _page_accuracy(model: tf.keras.Model, page: RealPage) -> float:
    predicted = _predict_symbols(model, page.image)
    mask = page.labels >= 0
    return float(np.mean(predicted[mask] == page.labels[mask]))


def _predict_symbols(model: tf.keras.Model, image: np.ndarray) -> np.ndarray:
    rows = image.shape[0] // CELL_PX
    predicted = np.zeros((rows, image.shape[1] // CELL_PX), np.int32)
    for start in range(0, rows, 32):
        predicted[start:start + 32] = _strip(model, image, start, min(rows, start + 32))
    return predicted


def _strip(model: tf.keras.Model, image: np.ndarray, start: int, stop: int) -> np.ndarray:
    halo = 2
    y0 = max(0, (start - halo) * CELL_PX)
    y1 = min(image.shape[0], (stop + halo) * CELL_PX)
    batch = tf.constant(image[y0:y1].astype(np.float32)[None] / 255.0)
    logits, _offset = model(batch, training=False)
    symbols = tf.argmax(logits, axis=-1, output_type=tf.int32).numpy()[0]
    out0 = (start * CELL_PX - y0) // CELL_PX
    return symbols[out0:out0 + stop - start]
