from PIL import Image

from common.glass_page import page_on_glass, page_replaced


def test_blank_and_dark_glass_are_empty() -> None:
    assert not page_on_glass(Image.new("RGB", (80, 100), (250, 250, 250)))
    assert not page_on_glass(Image.new("RGB", (80, 100), (8, 8, 8)))


def test_printed_page_is_detected_when_it_replaces_empty_glass() -> None:
    empty = Image.new("RGB", (160, 220), (12, 12, 12))
    page = Image.new("RGB", (160, 220), (245, 245, 240))
    for x in range(30, 130):
        for y in range(40, 120):
            if (x // 3 + y // 3) % 2 == 0:
                page.putpixel((x, y), (20, 30, 180))
    assert page_on_glass(page)
    assert page_replaced(empty, page)
    assert not page_replaced(page, page)
