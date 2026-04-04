import cv2
from PIL import Image

APRILTAG_FAMILY = "tag36h11"
APRILTAG_CV2_DICT = cv2.aruco.DICT_APRILTAG_36h11

TL_TAG_ID = 0
TR_TAG_ID = 1
BL_TAG_ID = 2
BR_TAG_ID = 3

CORNER_TAG_IDS = (TL_TAG_ID, TR_TAG_ID, BL_TAG_ID, BR_TAG_ID)
FLANK_TAG_IDS = (4, 5, 6, 7, 8, 9)

TAG_ID_TO_CORNER = {
    TL_TAG_ID: "tl",
    TR_TAG_ID: "tr",
    BL_TAG_ID: "bl",
    BR_TAG_ID: "br",
}


def _aruco_dict() -> cv2.aruco.Dictionary:
    return cv2.aruco.getPredefinedDictionary(APRILTAG_CV2_DICT)


def render_apriltag(tag_id: int, size_px: int) -> Image.Image:
    marker = cv2.aruco.generateImageMarker(_aruco_dict(), tag_id, size_px)
    return Image.fromarray(marker).convert("RGB")
