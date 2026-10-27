from PIL import Image, ImageDraw

from common.config import PaperClipConfig
from common.apriltag_markers import render_apriltag
from common.geometry_tags import tag_quiet_px
from common.page_layout import alignment_tag_placements, margin_offset


def draw_apriltag_layer(image: Image.Image, config: PaperClipConfig) -> Image.Image:
    mx, my = margin_offset(config)
    quiet = tag_quiet_px(config.print_dpi)
    draw = ImageDraw.Draw(image)
    for left, top, tag_id, size in alignment_tag_placements(config):
        x = mx + left
        y = my + top
        draw.rectangle(
            [x - quiet, y - quiet, x + size + quiet - 1, y + size + quiet - 1],
            fill=(255, 255, 255),
        )
        image.paste(render_apriltag(tag_id, size), (x, y))
    return image
