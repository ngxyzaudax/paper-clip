from PIL import Image


def page_on_glass(image: Image.Image) -> bool:
    pixels = list(_sample(image, 64, 88).get_flattened_data())
    total = len(pixels)
    bright = sum(1 for pixel in pixels if _bright(pixel))
    marked = sum(1 for pixel in pixels if _marked(pixel))
    return bright / total >= 0.35 and marked / total >= 0.03


def page_replaced(before: Image.Image, after: Image.Image) -> bool:
    if not page_on_glass(after):
        return False
    return _mean_delta(_sample(before, 32, 32), _sample(after, 32, 32)) >= 12


def _sample(image: Image.Image, width: int, height: int) -> Image.Image:
    return image.convert("RGB").resize((width, height), Image.Resampling.BOX)


def _bright(pixel: tuple[int, ...]) -> bool:
    red, green, blue = pixel[:3]
    return red > 150 and green > 150 and blue > 150


def _marked(pixel: tuple[int, ...]) -> bool:
    red, green, blue = pixel[:3]
    spread = abs(red - green) + abs(green - blue) + abs(blue - red)
    return (red + green + blue) < 520 or spread > 40


def _mean_delta(before: Image.Image, after: Image.Image) -> float:
    total = 0
    count = 0
    for left, right in zip(before.get_flattened_data(), after.get_flattened_data()):
        total += abs(left[0] - right[0]) + abs(left[1] - right[1]) + abs(left[2] - right[2])
        count += 3
    return total / count if count else 0.0
