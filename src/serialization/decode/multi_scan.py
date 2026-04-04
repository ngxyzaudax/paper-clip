import logging

import numpy as np

from common.types import HeaderData

logger = logging.getLogger(__name__)


def average_scans(
    raw_pages: list[tuple[int, np.ndarray, HeaderData]],
) -> list[tuple[int, np.ndarray, HeaderData]]:
    page_groups: dict[int, list[tuple[np.ndarray, HeaderData]]] = {}
    for page_idx, deskewed, header in raw_pages:
        page_groups.setdefault(page_idx, []).append((deskewed, header))

    result: list[tuple[int, np.ndarray, HeaderData]] = []
    for page_idx in sorted(page_groups):
        group = page_groups[page_idx]
        if len(group) > 1:
            logger.info("Averaging %d scans for page %d", len(group), page_idx)
            stacked = np.stack([img.astype(np.float32) for img, _ in group], axis=0)
            averaged = np.mean(stacked, axis=0).astype(np.uint8)
            result.append((page_idx, averaged, group[0][1]))
        else:
            result.append((page_idx, group[0][0], group[0][1]))
    return result
