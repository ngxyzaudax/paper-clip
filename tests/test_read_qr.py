import numpy as np

from common.config import resolve_config
from common.crypto import compute_sha256
from common.format_spec import QR_BORDER_MODULES
from common.geometry_qr import qr_module_px
from serialization.decode.read_qr import read_qr_header
from serialization.encode.qr_header import encode_header_bytes, qr_image

_CANVAS = 2800
_COLOURS = np.array([[0, 180, 220], [220, 40, 160], [40, 180, 60]], np.uint8)


def test_header_survives_dots_in_the_quiet_zone() -> None:
    config = resolve_config(cell_size_px=14, num_symbols=11, print_dpi=720)
    header = encode_header_bytes(config, 1, 2, 2, 190230, 122880, compute_sha256(b"round"), 0)
    code = np.asarray(qr_image(header, 1200, 0.22))
    canvas = _place(_speckle_quiet_zone(code, qr_module_px(1200, 0.22)))
    _image, decoded, points = read_qr_header(canvas)
    assert decoded.page_index == 1
    assert decoded.total_pages == 2
    assert decoded.cell_size_px == 14
    assert points is not None and len(points) == 4


def _speckle_quiet_zone(code: np.ndarray, module: int) -> np.ndarray:
    quiet = module * QR_BORDER_MODULES
    speckled = code.copy()
    speckled[:quiet, :] = _specks(speckled[:quiet, :].shape)
    speckled[-quiet:, :] = _specks(speckled[-quiet:, :].shape)
    speckled[:, :quiet] = _specks(speckled[:, :quiet].shape)
    speckled[:, -quiet:] = _specks(speckled[:, -quiet:].shape)
    return speckled


def _place(code: np.ndarray) -> np.ndarray:
    canvas = np.full((_CANVAS, _CANVAS, 3), 240, np.uint8)
    y_px = (_CANVAS - code.shape[0]) // 2
    x_px = (_CANVAS - code.shape[1]) // 2
    canvas[y_px:y_px + code.shape[0], x_px:x_px + code.shape[1]] = code
    return canvas


def _specks(shape: tuple[int, ...]) -> np.ndarray:
    picks = np.random.default_rng(3).integers(0, len(_COLOURS), size=shape[:2])
    return _COLOURS[picks]
