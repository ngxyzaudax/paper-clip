from PIL import Image

from common.apriltag_markers import BL_TAG_ID, BR_TAG_ID, TL_TAG_ID, TR_TAG_ID, render_apriltag
from common.config import PaperClipConfig
from common.page_layout import (
    finder_pattern_size,
    margin_offset,
    usable_area_px,
)


def draw_finder_patterns(image: Image.Image, config: PaperClipConfig) -> Image.Image:
    fp_size = finder_pattern_size(config)
    mx, my = margin_offset(config)
    usable_w, usable_h = usable_area_px(config)
    half = fp_size // 2
    corners = [
        (mx + half, my + half, TL_TAG_ID),
        (mx + usable_w - half, my + half, TR_TAG_ID),
        (mx + half, my + usable_h - half, BL_TAG_ID),
        (mx + usable_w - half, my + usable_h - half, BR_TAG_ID),
    ]
    for cx, cy, tag_id in corners:
        tag_img = render_apriltag(tag_id, fp_size)
        image.paste(tag_img, (cx - half, cy - half))
    return image
