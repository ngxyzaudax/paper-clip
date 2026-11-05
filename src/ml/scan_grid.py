from pathlib import Path
from typing import NamedTuple

import cv2
import numpy as np
from PIL import Image

from common.config import PaperClipConfig
from common.geometry import page_geometry
from common.geometry_types import PageGeometry
from common.page_layout import valid_cells_ordered
from ml.network import CELL_PX
from ml.scan_labels import labels_from_render
from serialization.decode.calibrate import calibration_offset_and_refs
from serialization.decode.classify import classify_cells
from serialization.decode.detect_tags import detect_tags
from serialization.decode.errors import DecodeError
from serialization.decode.header_config import config_from_header
from serialization.decode.load_scan import load_scans
from serialization.decode.read_qr import locate_qr_headers
from serialization.decode.restore import restore_page
from serialization.decode.warp_mesh import warp_page

class PageExample(NamedTuple):
    image: np.ndarray
    labels: np.ndarray
    page_index: int
    agreement: float


def write_page_examples(scan_dir: Path, digital_dir: Path, destination: Path) -> list[PageExample]:
    Image.MAX_IMAGE_PIXELS = None
    digital = png_pages(digital_dir)
    destination.mkdir(parents=True, exist_ok=True)
    pages = [_stored_example(path, digital, destination) for path in png_pages(scan_dir)]
    return sorted(pages, key=lambda item: item.page_index)


def load_page_examples(directory: Path) -> list[PageExample]:
    paths = sorted(directory.glob("page-*.npz"))
    if not paths:
        raise FileNotFoundError(f"no page examples in {directory}")
    return [_load(path) for path in paths]


def build_page_example(scan: np.ndarray, digital_paths: list[Path]) -> PageExample:
    located = locate_qr_headers(scan)
    if located is None:
        raise DecodeError("page header not found")
    rotated, hits = located
    header = hits[0].header
    if header.page_index >= len(digital_paths):
        raise DecodeError(f"scan is page {header.page_index + 1} but only {len(digital_paths)} digital pages exist")
    config = config_from_header(header)
    geometry = page_geometry(config)
    detected = detect_tags(rotated, {tag.tag_id for tag in geometry.tags})
    quads = tuple(hit.points for hit in hits if len(hit.points) == 4)
    warped = warp_page(rotated, geometry, detected, quads[0] if quads else None, tuple(quads[1:]))
    image = _resize_grid(warped, geometry)
    labels = labels_from_render(_open_rgb(digital_paths[header.page_index]), geometry, config)
    agreement = _agreement(warped, geometry, config, labels)
    if agreement < 0.9:
        raise DecodeError(f"page {header.page_index + 1} labels agree with the scan on only {agreement:.1%} of cells")
    return PageExample(image, labels, header.page_index, agreement)


def _resize_grid(warped: np.ndarray, geometry: PageGeometry) -> np.ndarray:
    y0, x0 = geometry.origin_y, geometry.origin_x
    cell, rows, cols = geometry.cell, geometry.rows, geometry.cols
    crop = warped[y0:y0 + rows * cell, x0:x0 + cols * cell]
    expected = (rows * cell, cols * cell, 3)
    if crop.shape != expected:
        raise DecodeError(f"warped grid is {crop.shape}, expected {expected}")
    return cv2.resize(crop, (cols * CELL_PX, rows * CELL_PX), interpolation=cv2.INTER_AREA)


def _agreement(
    warped: np.ndarray, geometry: PageGeometry, config: PaperClipConfig, labels: np.ndarray,
) -> float:
    colour = restore_page(warped)
    _dx, _dy, refs = calibration_offset_and_refs(colour, geometry, config)
    cells = valid_cells_ordered(config)
    symbols, _confidence = classify_cells(warped, geometry, config, 0, 0, refs, None, cells, colour)
    expected = np.array([int(labels[row, col]) for row, col in cells], np.int32)
    return float(np.mean(np.asarray(symbols) == expected))


def png_pages(directory: Path) -> list[Path]:
    paths = [item for item in sorted(directory.iterdir()) if item.suffix.lower() == ".png"]
    if not paths:
        raise FileNotFoundError(f"no PNG pages in {directory}")
    return paths


def _stored_example(path: Path, digital: list[Path], destination: Path) -> PageExample:
    print(f"labelling {path.name}", flush=True)
    page = build_page_example(load_scans(path)[0], digital)
    _save(destination / f"page-{page.page_index:02d}.npz", page)
    return page


def _open_rgb(path: Path) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGB"))


def _save(path: Path, page: PageExample) -> None:
    np.savez(
        path, image=page.image, labels=page.labels,
        page_index=np.int32(page.page_index), agreement=np.float32(page.agreement),
    )


def _load(path: Path) -> PageExample:
    stored = np.load(path)
    return PageExample(stored["image"], stored["labels"], int(stored["page_index"]), float(stored["agreement"]))
