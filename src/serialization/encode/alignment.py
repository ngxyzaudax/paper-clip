from PIL import Image

from common.config import PaperClipConfig
from common.apriltag_markers import render_apriltag
from common.page_layout import alignment_tag_placements, margin_offset


def draw_apriltag_layer(image: Image.Image, config: PaperClipConfig) -> Image.Image:
    mx, my = margin_offset(config)
    placements = alignment_tag_placements(config)
    for left, top, tag_id, size in placements:
        tag_img = render_apriltag(tag_id, size)
        image.paste(tag_img, (mx + left, my + top))
    return image
