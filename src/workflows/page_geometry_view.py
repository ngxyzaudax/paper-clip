from common.config import PaperClipConfig
from common.geometry import page_geometry
from common.geometry_types import HeaderSlot
from common.types import Region


def geometry_view(config: PaperClipConfig) -> dict[str, object]:
    geo = page_geometry(config)
    origin_x, origin_y = geo.origin_x, geo.origin_y
    return {
        "page": {"w": geo.page_w, "h": geo.page_h},
        "margins": {
            "x": origin_x,
            "y": origin_y,
            "w": geo.usable_w,
            "h": geo.usable_h,
        },
        "cell": geo.cell,
        "grid": {"cols": geo.cols, "rows": geo.rows},
        "slots": [_slot(slot, origin_x, origin_y) for slot in geo.slots],
        "tags": [
            {"id": tag.tag_id, "x": tag.x + origin_x, "y": tag.y + origin_y, "size": tag.size}
            for tag in geo.tags
        ],
    }


def _slot(slot: HeaderSlot, origin_x: int, origin_y: int) -> dict[str, object]:
    return {
        "block": _box(slot.block, origin_x, origin_y),
        "qr": _box(slot.qr, origin_x, origin_y),
        "calibration": _box(slot.calibration, origin_x, origin_y),
    }


def _box(region: Region, origin_x: int, origin_y: int) -> dict[str, int]:
    return {"x": region.x + origin_x, "y": region.y + origin_y, "w": region.width, "h": region.height}
