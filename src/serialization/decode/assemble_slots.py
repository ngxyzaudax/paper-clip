from typing import NamedTuple

from common.fountain import reconstruct_missing
from common.page_bytes import PageBytePlan
from serialization.decode.errors import DecodeError
from serialization.decode.observe import PageObservation
from serialization.decode.recover import recover_stream
from serialization.decode.repair import StreamRepair
from serialization.encode.qr_header import DecodedQrHeader

Slots = list[bytes | None]
ErasureMap = dict[int, list[int]]


class Assembly(NamedTuple):
    raw: bytes
    filename: str
    header: DecodedQrHeader
    repair: StreamRepair
    page_sizes: tuple[int, ...]
    rebuilt: tuple[int, ...]
    scanned: tuple[int, ...] = ()
    observed: tuple[PageObservation, ...] = ()


def decode_slots(
    slots: Slots,
    erasure_map: ErasureMap,
    header: DecodedQrHeader,
    plan: PageBytePlan,
    passphrase: str | None,
) -> Assembly:
    local_map = {key: list(value) for key, value in erasure_map.items()}
    rebuilt = tuple(index for index in range(header.data_pages) if slots[index] is None)
    data_slots = fill_missing(list(slots), header.data_pages, local_map)
    payload, erasures = _stream(data_slots, local_map, plan)
    if len(payload) != header.payload_length:
        raise DecodeError(f"assembled {len(payload)} payload bytes, header says {header.payload_length}")
    recovered = recover_stream(payload, header, erasures, passphrase)
    return Assembly(recovered.raw, recovered.filename, header, recovered.repair, tuple(plan.slice_len), rebuilt)


def _stream(data_slots: Slots, erasure_map: ErasureMap, plan: PageBytePlan) -> tuple[bytes, list[int]]:
    stream = bytearray()
    erasures: list[int] = []
    for index, part in enumerate(data_slots):
        take = plan.slice_len[index]
        if part is None or len(part) < take:
            raise DecodeError(f"data page {index} is incomplete")
        base = len(stream)
        stream.extend(part[:take])
        erasures.extend(base + item for item in erasure_map.get(index, []) if item < take)
    return bytes(stream), erasures


def fill_missing(slots: Slots, data_pages: int, erasure_map: ErasureMap) -> Slots:
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
