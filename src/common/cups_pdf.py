from pathlib import Path

from PIL import Image


def write_page_pdf(pages: list[Path], destination: Path) -> None:
    images = [Image.open(page).convert("RGB") for page in pages]
    try:
        images[0].save(
            destination,
            format="PDF",
            save_all=True,
            append_images=images[1:],
            resolution=_dpi(images[0]),
        )
    finally:
        for image in images:
            image.close()


def _dpi(image: Image.Image) -> float:
    raw = image.info.get("dpi", (720, 720))
    value = raw[0] if isinstance(raw, tuple) else raw
    return float(value or 720)
