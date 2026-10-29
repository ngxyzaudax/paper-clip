import xml.etree.ElementTree as ET
from typing import NamedTuple

from common.device_error import DeviceError

SCAN = "http://schemas.hp.com/imaging/escl/2011/05/03"
PWG = "http://www.pwg.org/schemas/2010/12/sm"
_NS = {"scan": SCAN, "pwg": PWG}


class ScannerCaps(NamedTuple):
    model: str
    max_width: int
    max_height: int
    resolutions: tuple[int, ...]
    color_modes: tuple[str, ...]
    formats: tuple[str, ...]
    source: str


def parse_capabilities(payload: bytes) -> ScannerCaps:
    root = ET.fromstring(payload)
    platen = root.find("scan:Platen/scan:PlatenInputCaps", _NS)
    node = platen if platen is not None else root
    modes = _texts(node, ".//scan:ColorMode")
    formats = _texts(node, ".//pwg:DocumentFormat") + _texts(node, ".//scan:DocumentFormatExt")
    return ScannerCaps(
        model=_text(root, "pwg:MakeAndModel"),
        max_width=_integer(node, "scan:MaxWidth") or 2480,
        max_height=_integer(node, "scan:MaxHeight") or 3508,
        resolutions=_resolutions(node),
        color_modes=tuple(dict.fromkeys(modes)),
        formats=tuple(dict.fromkeys(formats)),
        source="Platen" if root.find("scan:Platen", _NS) is not None else "Feeder",
    )


def scan_settings(caps: ScannerCaps, dpi: int) -> bytes:
    chosen = choose_dpi(caps.resolutions, dpi)
    color = "RGB24" if "RGB24" in caps.color_modes or not caps.color_modes else caps.color_modes[0]
    if color != "RGB24":
        raise DeviceError("scanner has no RGB24 color mode")
    if caps.formats and "image/jpeg" not in caps.formats:
        raise DeviceError("scanner has no JPEG document format")
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f'<scan:ScanSettings xmlns:scan="{SCAN}" xmlns:pwg="{PWG}">'
        "<pwg:Version>2.6</pwg:Version>"
        "<pwg:ScanRegions><pwg:ScanRegion>"
        "<pwg:ContentRegionUnits>escl:ThreeHundredthsOfInches</pwg:ContentRegionUnits>"
        "<pwg:XOffset>0</pwg:XOffset><pwg:YOffset>0</pwg:YOffset>"
        f"<pwg:Width>{caps.max_width}</pwg:Width><pwg:Height>{caps.max_height}</pwg:Height>"
        "</pwg:ScanRegion></pwg:ScanRegions>"
        f"<pwg:InputSource>{caps.source}</pwg:InputSource>"
        f"<pwg:ColorMode>{color}</pwg:ColorMode>"
        f"<scan:XResolution>{chosen}</scan:XResolution>"
        f"<scan:YResolution>{chosen}</scan:YResolution>"
        "<pwg:DocumentFormat>image/jpeg</pwg:DocumentFormat>"
        "</scan:ScanSettings>"
    )
    return xml.encode()


def choose_dpi(resolutions: tuple[int, ...], requested: int) -> int:
    if not resolutions:
        return requested
    if requested in resolutions:
        return requested
    under = [item for item in resolutions if item <= requested]
    pool = under or list(resolutions)
    return min(pool, key=lambda item: abs(item - requested))


def _resolutions(node: ET.Element) -> tuple[int, ...]:
    found: list[int] = []
    for item in node.findall(".//scan:DiscreteResolution", _NS):
        x_dpi = _integer(item, "scan:XResolution")
        y_dpi = _integer(item, "scan:YResolution")
        if x_dpi and x_dpi == y_dpi:
            found.append(x_dpi)
    return tuple(dict.fromkeys(found))


def _texts(node: ET.Element, path: str) -> list[str]:
    return [item.text for item in node.findall(path, _NS) if item.text]


def _text(node: ET.Element, path: str) -> str:
    found = node.find(path, _NS)
    return found.text or "" if found is not None and found.text else ""


def _integer(node: ET.Element, path: str) -> int:
    text = node.findtext(path, default="0", namespaces=_NS)
    return int(text or "0")
