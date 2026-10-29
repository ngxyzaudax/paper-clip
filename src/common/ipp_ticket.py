from common.ipp_codec import (
    attr_bool,
    attr_integer,
    attr_resolution,
    attr_text,
    begin_collection,
    end_collection,
    group,
    member,
    pack_message,
)
from common.ipp_options import PrintTicket

_REQUESTED = (
    "document-format-supported",
    "job-creation-attributes-supported",
    "media-bottom-margin-supported",
    "media-default",
    "media-left-margin-supported",
    "media-right-margin-supported",
    "media-source-supported",
    "media-supported",
    "media-top-margin-supported",
    "media-type-supported",
    "print-color-mode-supported",
    "print-quality-supported",
    "print-scaling-supported",
    "printer-make-and-model",
    "printer-resolution-supported",
    "printer-state",
    "pwg-raster-document-resolution-supported",
    "pwg-raster-document-type-supported",
    "sides-supported",
)


def get_attributes_request(uri: str) -> bytes:
    body = bytearray(group(0x01))
    body.extend(attr_text(0x47, "attributes-charset", "utf-8"))
    body.extend(attr_text(0x48, "attributes-natural-language", "en"))
    body.extend(attr_text(0x45, "printer-uri", uri))
    body.extend(attr_text(0x44, "requested-attributes", _REQUESTED[0]))
    for name in _REQUESTED[1:]:
        body.extend(attr_text(0x44, "", name))
    return pack_message(0x000B, 1, bytes(body))


def job_request(operation: int, uri: str, title: str, ticket: PrintTicket, document: bytes = b"") -> bytes:
    body = _operation_group(uri, title, ticket.document_format) + _job_group(ticket)
    return pack_message(operation, 2, body) + document


def job_status_request(uri: str, job_id: int) -> bytes:
    body = bytearray(group(0x01))
    body.extend(attr_text(0x47, "attributes-charset", "utf-8"))
    body.extend(attr_text(0x48, "attributes-natural-language", "en"))
    body.extend(attr_text(0x45, "printer-uri", uri))
    body.extend(attr_integer(0x21, "job-id", job_id))
    body.extend(attr_text(0x44, "requested-attributes", "job-state"))
    body.extend(attr_text(0x44, "", "job-state-reasons"))
    return pack_message(0x0009, 3, bytes(body))


def _operation_group(uri: str, title: str, document_format: str) -> bytes:
    return b"".join((
        group(0x01),
        attr_text(0x47, "attributes-charset", "utf-8"),
        attr_text(0x48, "attributes-natural-language", "en"),
        attr_text(0x45, "printer-uri", uri),
        attr_text(0x42, "requesting-user-name", "paper-clip"),
        attr_text(0x42, "job-name", title[:127]),
        attr_text(0x49, "document-format", document_format),
        attr_bool("ipp-attribute-fidelity", True),
    ))


def _job_group(ticket: PrintTicket) -> bytes:
    parts = [
        group(0x02),
        attr_text(0x44, "media", ticket.media.keyword),
        begin_collection("media-col"),
        member("media-size"),
        begin_collection(""),
        member("x-dimension"),
        attr_integer(0x21, "", ticket.media.hundredths[0]),
        member("y-dimension"),
        attr_integer(0x21, "", ticket.media.hundredths[1]),
        end_collection(),
        member("media-top-margin"),
        attr_integer(0x21, "", ticket.margin),
        member("media-bottom-margin"),
        attr_integer(0x21, "", ticket.margin),
        member("media-left-margin"),
        attr_integer(0x21, "", ticket.margin),
        member("media-right-margin"),
        attr_integer(0x21, "", ticket.margin),
        member("media-source"),
        attr_text(0x44, "", ticket.source),
        member("media-type"),
        attr_text(0x44, "", "stationery"),
        end_collection(),
        attr_text(0x44, "print-color-mode", ticket.color),
        attr_integer(0x23, "print-quality", ticket.quality),
        attr_text(0x44, "print-scaling", ticket.scaling),
        attr_text(0x44, "sides", ticket.sides),
        *_resolution(ticket),
    ]
    return b"".join(parts)


def _resolution(ticket: PrintTicket) -> tuple[bytes, ...]:
    if ticket.document_format == "image/pwg-raster":
        return ()
    return (attr_resolution("printer-resolution", ticket.dpi, ticket.dpi),)
