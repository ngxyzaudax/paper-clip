from common.device_error import DeviceError
from common.ipp_choices import choose_document, choose_duplex
from common.ipp_codec import IppMap

_NO_DUPLEX = "This printer does not advertise duplex."
_NO_PWG = "This printer cannot put both sides in one PWG document."


def printable_duplex(attributes: IppMap) -> str | None:
    duplex = choose_duplex(attributes)
    if duplex is None or _document_format(attributes) != "image/pwg-raster":
        return None
    return duplex


def require_duplex(attributes: IppMap) -> str:
    duplex = printable_duplex(attributes)
    if duplex is None:
        raise DeviceError(_failure(attributes))
    return duplex


def _document_format(attributes: IppMap) -> str:
    document_format, _dpi = choose_document(attributes)
    return document_format


def _failure(attributes: IppMap) -> str:
    if choose_duplex(attributes) is None:
        return _NO_DUPLEX
    return _NO_PWG
