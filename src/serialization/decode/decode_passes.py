from collections.abc import Callable

import numpy as np

from serialization.decode.errors import DecodeError
from serialization.decode.observation import PageObservation
from serialization.decode.observe import observe_page
from serialization.encode.qr_header import DecodedQrHeader

OnDecodeProgress = Callable[[int, int, str], None]


def first_pass(
    images: list[np.ndarray],
    model: object | None,
    on_page: OnDecodeProgress | None,
) -> tuple[list[PageObservation], list[np.ndarray]]:
    pages: list[PageObservation] = []
    pending: list[np.ndarray] = []
    total = len(images)
    for index, image in enumerate(images):
        report_progress(on_page, index, total, "read")
        try:
            pages.append(observe_page(image, model))
        except DecodeError:
            pending.append(image)
    return pages, pending


def retry_pass(
    pending: list[np.ndarray],
    model: object | None,
    hints: tuple[DecodedQrHeader, ...],
    total: int,
    on_page: OnDecodeProgress | None,
) -> list[PageObservation]:
    found: list[PageObservation] = []
    for index, image in enumerate(pending):
        report_progress(on_page, index, total, "retry")
        try:
            found.append(observe_page(image, model, hints))
        except DecodeError:
            continue
    return found


def report_progress(on_page: OnDecodeProgress | None, index: int, total: int, stage: str) -> None:
    if on_page:
        on_page(index, total, stage)
