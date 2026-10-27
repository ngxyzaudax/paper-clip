import cv2
import numpy as np

_STEP = 8
_SMOOTHING = 1e-4


def warp_tps(
    image: np.ndarray,
    inverse: np.ndarray,
    ideal: np.ndarray,
    observed: np.ndarray,
    width: int,
    height: int,
) -> np.ndarray:
    scale = float(max(width, height))
    nodes = ideal.astype(np.float64) / scale
    residual = observed.astype(np.float64) - _project_many(inverse, ideal.astype(np.float64))
    weights = _fit(nodes, residual)
    grid_x, grid_y = _coarse_grid(width, height)
    points = np.stack([grid_x.ravel(), grid_y.ravel()], axis=1)
    mapped = _project_many(inverse, points) + _evaluate(nodes, weights, points / scale)
    map_x = _upsample(mapped[:, 0].reshape(grid_x.shape), width, height)
    map_y = _upsample(mapped[:, 1].reshape(grid_x.shape), width, height)
    return cv2.remap(
        image, map_x, map_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255),
    )


def _kernel(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    dist2 = np.sum((a[:, None, :] - b[None, :, :]) ** 2, axis=2)
    with np.errstate(divide="ignore", invalid="ignore"):
        values = 0.5 * dist2 * np.log(dist2)
    return np.nan_to_num(values, nan=0.0, posinf=0.0, neginf=0.0)


def _affine_basis(points: np.ndarray) -> np.ndarray:
    return np.hstack([np.ones((len(points), 1)), points])


def _fit(nodes: np.ndarray, values: np.ndarray) -> np.ndarray:
    count = len(nodes)
    basis = _affine_basis(nodes)
    system = np.zeros((count + 3, count + 3))
    system[:count, :count] = _kernel(nodes, nodes) + _SMOOTHING * np.eye(count)
    system[:count, count:] = basis
    system[count:, :count] = basis.T
    rhs = np.zeros((count + 3, 2))
    rhs[:count] = values
    return np.linalg.lstsq(system, rhs, rcond=None)[0]


def _evaluate(nodes: np.ndarray, weights: np.ndarray, points: np.ndarray) -> np.ndarray:
    count = len(nodes)
    return _kernel(points, nodes) @ weights[:count] + _affine_basis(points) @ weights[count:]


def _project_many(matrix: np.ndarray, points: np.ndarray) -> np.ndarray:
    homogeneous = np.hstack([points, np.ones((len(points), 1))]) @ matrix.T
    depth = homogeneous[:, 2:3]
    depth = np.where(np.abs(depth) < 1e-12, 1e-12, depth)
    return homogeneous[:, :2] / depth


def _coarse_grid(width: int, height: int) -> tuple[np.ndarray, np.ndarray]:
    offset = (_STEP - 1) / 2.0
    xs = np.arange(-(-width // _STEP)) * _STEP + offset
    ys = np.arange(-(-height // _STEP)) * _STEP + offset
    return np.meshgrid(xs, ys)


def _upsample(values: np.ndarray, width: int, height: int) -> np.ndarray:
    rows, cols = values.shape
    full = cv2.resize(values.astype(np.float32), (cols * _STEP, rows * _STEP), interpolation=cv2.INTER_LINEAR)
    return np.ascontiguousarray(full[:height, :width])
