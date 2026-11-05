from dataclasses import replace

from common.compression import compress
from common.config import PaperClipConfig, validate_config
from common.encryption import ENCRYPTION_OVERHEAD
from common.format_spec import ECC_MAX
from common.page_layout import data_capacity_bytes, pages_needed
from serialization.encode.frame_payload import interleaved_length


def fill_config(raw: bytes, config: PaperClipConfig, filename: str) -> PaperClipConfig:
    ecc = largest_ecc(*encoded_lengths(raw, filename), config)
    if ecc == config.ecc_sym:
        return config
    return validate_config(replace(config, ecc_sym=ecc))


def encoded_lengths(raw: bytes, filename: str) -> tuple[int, int]:
    return len(compress(raw)) + ENCRYPTION_OVERHEAD, len(filename.encode("utf-8")[:255])


def largest_ecc(blob_len: int, name_len: int, config: PaperClipConfig) -> int:
    floor = config.ecc_sym
    pages = pages_needed(interleaved_length(blob_len, name_len, floor), config)
    room = data_capacity_bytes(config) * pages
    return _search(blob_len, name_len, floor, room)


def _search(blob_len: int, name_len: int, floor: int, room: int) -> int:
    lo, hi, best = floor, ECC_MAX, floor
    while lo <= hi:
        mid = (lo + hi) // 2
        if interleaved_length(blob_len, name_len, mid) <= room:
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1
    return best
