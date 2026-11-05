import cv2
import numpy as np

from serialization.decode.qr_centre import _origin


def test_a_rotated_crop_keeps_its_place() -> None:
    image = np.arange(50 * 80, dtype=np.uint8).reshape(50, 80)
    x_px, y_px, width, height = 10, 15, 8, 6
    crop = image[y_px:y_px + height, x_px:x_px + width]
    turns = (None, cv2.ROTATE_90_CLOCKWISE, cv2.ROTATE_180, cv2.ROTATE_90_COUNTERCLOCKWISE)
    for index, code in enumerate(turns):
        rotated = image if code is None else cv2.rotate(image, code)
        rotated_crop = crop if code is None else cv2.rotate(crop, code)
        origin = _origin(image.shape, x_px, y_px, width, height, index)
        col, row = int(origin[0]), int(origin[1])
        view = rotated[row:row + rotated_crop.shape[0], col:col + rotated_crop.shape[1]]
        assert np.array_equal(view, rotated_crop)
