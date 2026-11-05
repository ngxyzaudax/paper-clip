from common.page_bytes import PageBytePlan
from serialization.decode.assemble_slots import Assembly, ErasureMap, Slots, decode_slots
from serialization.decode.errors import DecodeError, PassphraseError
from serialization.encode.qr_header import DecodedQrHeader

_STREAM_FAILURES = (
    "Reed-Solomon",
    "SHA-256",
    "decryption or decompression failed",
    "original length mismatch",
)


def rescue_failed_page(
    slots: Slots,
    erasure_map: ErasureMap,
    header: DecodedQrHeader,
    plan: PageBytePlan,
    passphrase: str | None,
    exc: DecodeError,
) -> Assembly | None:
    """Retry with the most damaged data page dropped, so page parity rebuilds it instead."""
    if header.total_pages <= header.data_pages or not _stream_failed(exc):
        return None
    present = [index for index in range(header.data_pages) if slots[index] is not None]
    if not _spare_parity(slots, header, len(present)):
        return None
    present.sort(key=lambda index: len(erasure_map.get(index, ())), reverse=True)
    for index in present:
        trial = list(slots)
        trial[index] = None
        try:
            return decode_slots(trial, erasure_map, header, plan, passphrase)
        except DecodeError:
            continue
    return None


def _spare_parity(slots: Slots, header: DecodedQrHeader, present: int) -> bool:
    missing = header.data_pages - present
    parity = sum(slots[index] is not None for index in range(header.data_pages, header.total_pages))
    return parity - missing >= 1


def _stream_failed(exc: DecodeError) -> bool:
    return not isinstance(exc, PassphraseError) and any(marker in str(exc) for marker in _STREAM_FAILURES)
