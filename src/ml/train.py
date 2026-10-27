import os
from pathlib import Path

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")

import numpy as np
import tensorflow as tf

from ml.network import build_cell_decoder
from ml.store import default_model_path
from ml.synthetic import sample_batch


def train_cell_decoder(
    steps: int = 400,
    batch_size: int = 8,
    output_path: Path | None = None,
    seed: int = 7,
) -> tuple[Path, float]:
    rng = np.random.default_rng(seed)
    tf.random.set_seed(seed)
    model = build_cell_decoder()
    optimizer = tf.keras.optimizers.Adam(1e-3)
    accuracy = 0.0
    for step in range(steps):
        images, labels, offsets = sample_batch(batch_size, rng)
        loss, accuracy = _train_step(model, optimizer, images, labels, offsets)
        if step % 20 == 0 or step + 1 == steps:
            print(f"step {step + 1}/{steps} loss {float(loss):.4f} accuracy {float(accuracy):.3f}", flush=True)
    accuracy = _held_out_accuracy(model, rng)
    print(f"held-out accuracy {accuracy:.3f}", flush=True)
    destination = output_path or default_model_path()
    destination.parent.mkdir(parents=True, exist_ok=True)
    model.save(str(destination))
    return destination, accuracy


def _held_out_accuracy(model: tf.keras.Model, rng: np.random.Generator) -> float:
    images, labels, _offsets = sample_batch(16, rng)
    logits, _predicted = model(tf.constant(images), training=False)
    predicted = tf.argmax(logits, axis=-1, output_type=tf.int32)
    matches = tf.equal(predicted, tf.constant(labels))
    return float(tf.reduce_mean(tf.cast(matches, tf.float32)))


@tf.function(reduce_retracing=True)
def _train_step(
    model: tf.keras.Model,
    optimizer: tf.keras.optimizers.Optimizer,
    images: np.ndarray,
    labels: np.ndarray,
    offsets: np.ndarray,
) -> tuple[tf.Tensor, tf.Tensor]:
    with tf.GradientTape() as tape:
        logits, predicted = model(images, training=True)
        cross = tf.keras.losses.sparse_categorical_crossentropy(labels, logits, from_logits=True)
        loss = tf.reduce_mean(cross) + 0.15 * tf.reduce_mean(tf.square(predicted - offsets))
    gradients = tape.gradient(loss, model.trainable_variables)
    optimizer.apply_gradients(zip(gradients, model.trainable_variables))
    matches = tf.equal(tf.argmax(logits, axis=-1, output_type=tf.int32), labels)
    return loss, tf.reduce_mean(tf.cast(matches, tf.float32))
