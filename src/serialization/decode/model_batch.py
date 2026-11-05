from collections.abc import Iterator

import numpy as np

from serialization.decode.model_strips import CELL_PX, Strip, groups, output_row, strips

_BATCH = 8


def forward_grid(model: object, image: np.ndarray) -> tuple[np.ndarray, np.ndarray | None]:
    tiles = strips(image.shape[0] // CELL_PX)
    pieces = _pieces(model, image, tiles)
    return _assemble(image.shape[0] // CELL_PX, image.shape[1] // CELL_PX, pieces)


def _pieces(
    model: object, image: np.ndarray, tiles: tuple[Strip, ...],
) -> tuple[tuple[Strip, np.ndarray, np.ndarray | None], ...]:
    tensor = _tensorflow().convert_to_tensor(image)
    width = int(image.shape[1])
    return tuple(
        piece
        for group in groups(tiles)
        for piece in _evaluate(model, tensor, width, group)
    )


def _evaluate(
    model: object, tensor: object, width: int, group: tuple[Strip, ...],
) -> tuple[tuple[Strip, np.ndarray, np.ndarray | None], ...]:
    outputs = tuple(_predict(model, _dataset(tensor, width, group)))
    logits = np.concatenate([item[0] for item in outputs], axis=0)
    offset = _join_offset(outputs)
    return tuple(
        (strip, logits[index], None if offset is None else offset[index])
        for index, strip in enumerate(group)
    )


def _assemble(
    rows: int,
    cols: int,
    pieces: tuple[tuple[Strip, np.ndarray, np.ndarray | None], ...],
) -> tuple[np.ndarray, np.ndarray | None]:
    logits = np.empty((rows, cols, pieces[0][1].shape[-1]), np.float32)
    offset = _blank_offset(rows, cols, pieces[0][2])
    for strip, tile_logits, tile_offset in pieces:
        _place(strip, tile_logits, tile_offset, logits, offset)
    return logits, offset


def _blank_offset(rows: int, cols: int, sample: np.ndarray | None) -> np.ndarray | None:
    if sample is None:
        return None
    return np.empty((rows, cols, sample.shape[-1]), np.float32)


def _place(
    strip: Strip,
    tile_logits: np.ndarray,
    tile_offset: np.ndarray | None,
    logits: np.ndarray,
    offset: np.ndarray | None,
) -> None:
    start = output_row(strip)
    count = strip.row1 - strip.row0
    logits[strip.row0:strip.row1] = tile_logits[start:start + count]
    if offset is not None and tile_offset is not None:
        offset[strip.row0:strip.row1] = tile_offset[start:start + count]


def _dataset(tensor: object, width: int, group: tuple[Strip, ...]) -> object:
    tf = _tensorflow()
    height = group[0].y1 - group[0].y0
    starts = tf.constant([item.y0 for item in group], tf.int32)

    def take(start: object) -> object:
        return tf.slice(tensor, [start, 0, 0], [height, width, 3])

    return (
        tf.data.Dataset.from_tensor_slices(starts)
        .map(take, num_parallel_calls=tf.data.AUTOTUNE)
        .batch(_BATCH)
        .prefetch(tf.data.AUTOTUNE)
    )


def _predict(model: object, dataset: object) -> Iterator[tuple[np.ndarray, np.ndarray | None]]:
    for batch in dataset:
        yield _outputs(model(batch, training=False))


def _outputs(output: object) -> tuple[np.ndarray, np.ndarray | None]:
    if isinstance(output, (list, tuple)):
        logits = np.asarray(output[0])
        offset = np.asarray(output[1]) if len(output) > 1 else None
        return logits, offset
    return np.asarray(output), None


def _join_offset(
    outputs: tuple[tuple[np.ndarray, np.ndarray | None], ...],
) -> np.ndarray | None:
    if outputs[0][1] is None:
        return None
    return np.concatenate([item[1] for item in outputs], axis=0)


def _tensorflow() -> object:
    import tensorflow as tf

    return tf
