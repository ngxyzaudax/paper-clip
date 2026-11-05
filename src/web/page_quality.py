import logging

import numpy as np

from serialization.decode.errors import DecodeError
from serialization.decode.observe import observe_page
from serialization.decode.observation import PageObservation

logger = logging.getLogger(__name__)


def page_quality(image: np.ndarray) -> dict[str, object]:
    try:
        return _label(observe_page(image, None))
    except (DecodeError, ValueError, OSError):
        logger.exception("Page quality could not be read")
        return {"quality": "unread", "erasures": None}


def _label(page: PageObservation) -> dict[str, object]:
    if _reprint(page):
        return _quality("reprint", len(page.erasures))
    if _faint(page):
        return _quality("faint", len(page.erasures))
    return _quality("good", len(page.erasures))


def _reprint(page: PageObservation) -> bool:
    return page.qr_copies_read <= 1 or page.header_source == "orphan"


def _faint(page: PageObservation) -> bool:
    return len(page.erasures) / max(1, len(page.symbols)) > 0.02


def _quality(label: str, erasures: int) -> dict[str, object]:
    return {"quality": label, "erasures": erasures}
