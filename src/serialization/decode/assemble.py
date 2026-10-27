from common.fountain import reconstruct_missing
from common.page_bytes import page_byte_plan
from common.page_layout import data_capacity_bytes
from serialization.decode.errors import DecodeError
from serialization.decode.header_config import config_from_header
from serialization.decode.observe import PageObservation
from serialization.decode.recover import recover_stream


def assemble_pages(pages: list[PageObservation], passphrase: str | None) -> tuple[bytes, str]:
    if not pages:
        raise DecodeError("no pages were decoded")
    header = _compatible_header(pages)
    chosen = _best_by_index(pages)
    config = config_from_header(header)
    plan = page_byte_plan(
        header.payload_length, data_capacity_bytes(config), header.data_pages, header.num_symbols,
    )
    slots: list[bytes | None] = [None] * header.total_pages
    erasure_map: dict[int, list[int]] = {}
    for index, page in chosen.items():
        slots[index] = page.data
        erasure_map[index] = list(page.erasures)
    data_slots = _fill_missing(slots, header.data_pages, erasure_map)
    stream = bytearray()
    erasures: list[int] = []
    for index, part in enumerate(data_slots):
        take = plan.slice_len[index]
        if part is None or len(part) < take:
            raise DecodeError(f"data page {index} is incomplete")
        base = len(stream)
        stream.extend(part[:take])
        erasures.extend(base + item for item in erasure_map.get(index, []) if item < take)
    payload = bytes(stream)
    if len(payload) != header.payload_length:
        raise DecodeError(
            f"assembled {len(payload)} payload bytes, header says {header.payload_length}"
        )
    return recover_stream(payload, header, erasures, passphrase)


def _compatible_header(pages: list[PageObservation]):
    header = pages[0].header
    for page in pages[1:]:
        other = page.header
        if (
            other.original_sha256 != header.original_sha256
            or other.payload_length != header.payload_length
            or other.total_pages != header.total_pages
            or other.data_pages != header.data_pages
        ):
            raise DecodeError("scan pages do not belong to the same document")
    return header


def _best_by_index(pages: list[PageObservation]) -> dict[int, PageObservation]:
    chosen: dict[int, PageObservation] = {}
    for page in pages:
        index = page.header.page_index
        if index < 0 or index >= page.header.total_pages:
            raise DecodeError(f"page index {index} is outside the document")
        previous = chosen.get(index)
        if previous is None or len(page.erasures) < len(previous.erasures):
            chosen[index] = page
    return chosen


def _fill_missing(
    slots: list[bytes | None], data_pages: int, erasure_map: dict[int, list[int]],
) -> list[bytes | None]:
    data_slots = slots[:data_pages]
    if all(part is not None for part in data_slots):
        return data_slots
    redundancy = len(slots) - data_pages
    if redundancy <= 0:
        missing = [index for index, part in enumerate(data_slots) if part is None]
        raise DecodeError(f"missing data pages {missing} and no parity pages were scanned")
    try:
        restored = reconstruct_missing(slots, data_pages, redundancy)
    except Exception as exc:
        raise DecodeError(f"page parity reconstruction failed: {exc}") from exc
    for index, part in enumerate(data_slots):
        if part is None:
            data_slots[index] = restored[index]
            erasure_map[index] = []
    return data_slots
