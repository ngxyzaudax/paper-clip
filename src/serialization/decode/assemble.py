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
    try:
        return _decode_slots(slots, erasure_map, header, plan, passphrase)
    except DecodeError as exc:
        rescued = _rescue_failed_page(slots, erasure_map, header, plan, passphrase, exc)
        if rescued is None:
            raise
        return rescued


def _decode_slots(
    slots: list[bytes | None],
    erasure_map: dict[int, list[int]],
    header,
    plan,
    passphrase: str | None,
) -> tuple[bytes, str]:
    local_map = {key: list(value) for key, value in erasure_map.items()}
    data_slots = _fill_missing(list(slots), header.data_pages, local_map)
    stream = bytearray()
    erasures: list[int] = []
    for index, part in enumerate(data_slots):
        take = plan.slice_len[index]
        if part is None or len(part) < take:
            raise DecodeError(f"data page {index} is incomplete")
        base = len(stream)
        stream.extend(part[:take])
        erasures.extend(base + item for item in local_map.get(index, []) if item < take)
    payload = bytes(stream)
    if len(payload) != header.payload_length:
        raise DecodeError(
            f"assembled {len(payload)} payload bytes, header says {header.payload_length}"
        )
    return recover_stream(payload, header, erasures, passphrase)


def _rescue_failed_page(
    slots: list[bytes | None],
    erasure_map: dict[int, list[int]],
    header,
    plan,
    passphrase: str | None,
    exc: DecodeError,
) -> tuple[bytes, str] | None:
    if header.total_pages <= header.data_pages or not _stream_failed(exc):
        return None
    present = [index for index in range(header.data_pages) if slots[index] is not None]
    present.sort(key=lambda index: len(erasure_map.get(index, ())), reverse=True)
    missing = header.data_pages - len(present)
    watched = range(header.data_pages, header.total_pages)
    if sum(slots[index] is not None for index in watched) - missing < 1:
        return None
    for index in present:
        trial = list(slots)
        trial[index] = None
        try:
            return _decode_slots(trial, erasure_map, header, plan, passphrase)
        except DecodeError:
            continue
    return None


def _stream_failed(exc: DecodeError) -> bool:
    text = str(exc)
    return (
        "Reed-Solomon" in text
        or "SHA-256" in text
        or "decryption or decompression failed" in text
        or "original length mismatch" in text
    )


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
