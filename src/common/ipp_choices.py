from common.device_error import DeviceError
from common.ipp_codec import IppMap
from common.ipp_media import MEDIA_SIZES, MediaSize

_FEEDS = ("main", "tray-1", "tray-2", "auto")
_MARGIN_KEYS = (
    "media-top-margin-supported",
    "media-bottom-margin-supported",
    "media-left-margin-supported",
    "media-right-margin-supported",
)
_PWG_DPI = (720, 600, 360, 300)


def choose_media(attributes: IppMap, paper: str) -> MediaSize:
    if paper not in MEDIA_SIZES:
        raise DeviceError(f"unsupported paper size: {paper}")
    media = MEDIA_SIZES[paper]
    supported = _keywords(attributes, "media-supported")
    if supported and media.keyword not in supported:
        raise DeviceError(f"printer does not list bordered media {media.keyword}")
    return media


def choose_source(attributes: IppMap) -> str:
    supported = _keywords(attributes, "media-source-supported")
    if not supported:
        return "main"
    for name in _FEEDS:
        if name in supported:
            return name
    raise DeviceError("printer has no cassette (main) or auto media source")


def choose_margin(attributes: IppMap) -> int:
    listed = [key for key in _MARGIN_KEYS if attributes.get(key)]
    if not listed:
        return 300
    choices = [_required_positive(attributes, key) for key in listed]
    common = set.intersection(*choices)
    if not common:
        raise DeviceError("printer has no margin that is bordered on every side")
    return min(common)


def choose_color(attributes: IppMap) -> str:
    supported = _keywords(attributes, "print-color-mode-supported")
    if not supported or "color" in supported:
        return "color"
    raise DeviceError("printer has no color mode")


def choose_quality(attributes: IppMap) -> int:
    supported = [int(item) for item in attributes.get("print-quality-supported", []) if isinstance(item, int)]
    if not supported or 5 in supported:
        return 5
    if 4 in supported:
        return 4
    return supported[0]


def choose_scaling(attributes: IppMap) -> str:
    supported = _keywords(attributes, "print-scaling-supported")
    if supported and "none" not in supported:
        raise DeviceError("printer cannot print at 100% scale")
    return "none"


def choose_sides(attributes: IppMap) -> str:
    supported = _keywords(attributes, "sides-supported")
    if supported and "one-sided" not in supported:
        raise DeviceError("printer cannot print single-sided")
    return "one-sided"


def choose_document(attributes: IppMap) -> tuple[str, int]:
    formats = _keywords(attributes, "document-format-supported")
    if "image/pwg-raster" in formats or not formats:
        return "image/pwg-raster", _pwg_dpi(attributes)
    if "image/jpeg" in formats:
        return "image/jpeg", 360
    raise DeviceError("printer offers no driverless PWG raster or JPEG document format")


def can_send(attributes: IppMap, name: str) -> bool:
    created = [str(item) for item in attributes.get("job-creation-attributes-supported", [])]
    return not created or name in created


def _keywords(attributes: IppMap, name: str) -> list[str]:
    return [str(item) for item in attributes.get(name, [])]


def _required_positive(attributes: IppMap, key: str) -> set[int]:
    positive = {int(item) for item in attributes.get(key, []) if isinstance(item, int) and item > 0}
    if not positive:
        raise DeviceError("printer has no bordered margin")
    return positive


def _pwg_dpi(attributes: IppMap) -> int:
    found = [
        int(item[0])
        for item in attributes.get("pwg-raster-document-resolution-supported", [])
        if isinstance(item, tuple) and len(item) >= 2 and item[0] == item[1]
    ]
    for choice in _PWG_DPI:
        if choice in found:
            return choice
    under = [item for item in found if item <= 720]
    if under:
        return max(under)
    return min(found) if found else 360
