from typing import NamedTuple

from common.device_error import DeviceError
from common.ipp_choices import (
    can_send,
    choose_color,
    choose_document,
    choose_margin,
    choose_media,
    choose_quality,
    choose_scaling,
    choose_sides,
    choose_source,
)
from common.ipp_codec import IppMap
from common.ipp_media import MediaSize

_REQUIRED = ("media-col", "print-scaling", "print-color-mode", "sides")


class PrintTicket(NamedTuple):
    media: MediaSize
    source: str
    margin: int
    color: str
    quality: int
    scaling: str
    sides: str
    dpi: int
    document_format: str


def build_ticket(attributes: IppMap, paper: str) -> PrintTicket:
    document_format, dpi = choose_document(attributes)
    ticket = PrintTicket(
        media=choose_media(attributes, paper),
        source=choose_source(attributes),
        margin=choose_margin(attributes),
        color=choose_color(attributes),
        quality=choose_quality(attributes),
        scaling=choose_scaling(attributes),
        sides=choose_sides(attributes),
        dpi=dpi,
        document_format=document_format,
    )
    if ticket.margin <= 0 or ticket.scaling != "none" or "borderless" in ticket.media.keyword.lower():
        raise DeviceError("refusing a borderless or fit-to-page ticket")
    missing = [name for name in _REQUIRED if not can_send(attributes, name)]
    if missing:
        raise DeviceError("printer does not accept " + ", ".join(missing))
    return ticket
