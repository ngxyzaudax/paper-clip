import numpy as np


def _shape_chain(orig_cols: int, orig_rows: int, k: int) -> list[tuple[int, int]]:
    rows, cols = orig_rows, orig_cols
    shapes = [(rows, cols)]
    for _ in range(k):
        rows, cols = cols, rows
        shapes.append((rows, cols))
    return shapes


def map_cw_rotated_to_original(
    x: float, y: float, k: int, orig_cols: int, orig_rows: int,
) -> tuple[float, float]:
    if k % 4 == 0:
        return x, y
    k = k % 4
    shapes = _shape_chain(orig_cols, orig_rows, k)
    xr, yr = float(x), float(y)
    for i in range(k, 0, -1):
        r_old, _ = shapes[i - 1]
        x_old = yr
        y_old = float(r_old) - 1.0 - xr
        xr, yr = x_old, y_old
    return xr, yr


def map_original_to_cw_rotated(
    x: float, y: float, k: int, orig_cols: int, orig_rows: int,
) -> tuple[float, float]:
    if k % 4 == 0:
        return x, y
    k = k % 4
    shapes = _shape_chain(orig_cols, orig_rows, k)
    xr, yr = float(x), float(y)
    for i in range(1, k + 1):
        r_old, _ = shapes[i - 1]
        x_new = float(r_old) - 1.0 - yr
        y_new = xr
        xr, yr = x_new, y_new
    return xr, yr


def verify_mapping() -> None:
    import cv2
    h, w = 100, 200
    img = np.zeros((h, w), np.uint8)
    img[10, 50] = 255
    for k in range(4):
        r = img.copy()
        for _ in range(k):
            r = cv2.rotate(r, cv2.ROTATE_90_CLOCKWISE)
        pos = np.argwhere(r == 255)
        if len(pos) == 0:
            raise RuntimeError(f"k={k} no pixel")
        yr, xr = float(pos[0][0]), float(pos[0][1])
        bx, by = map_cw_rotated_to_original(xr, yr, k, w, h)
        if abs(bx - 50) > 0.1 or abs(by - 10) > 0.1:
            raise RuntimeError(f"k={k} got ({bx},{by}) expected (50,10) from ({xr},{yr})")
        fx, fy = map_original_to_cw_rotated(50.0, 10.0, k, w, h)
        if abs(fx - xr) > 0.1 or abs(fy - yr) > 0.1:
            raise RuntimeError(f"k={k} roundtrip forward ({fx},{fy}) vs ({xr},{yr})")


if __name__ == "__main__":
    verify_mapping()
    print("orientation mapping verification passed")
