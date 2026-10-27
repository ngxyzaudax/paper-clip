import math
from typing import NamedTuple

from common.codec import effective_block_size
from common.format_spec import PAYLOAD_HEADER_REDUNDANCY, PAYLOAD_HEADER_STRUCT


class PreparedPayload(NamedTuple):
    payload: bytes
    original_sha256: bytes
    original_length: int
    flags: int


def frame_body(blob: bytes, filename: str, block_size: int) -> tuple[bytes, int]:
    fname = filename.encode("utf-8")[:255]
    raw_len = PAYLOAD_HEADER_STRUCT.size * PAYLOAD_HEADER_REDUNDANCY + len(fname) + len(blob)
    num_blocks = max(1, int(math.ceil(raw_len / block_size)))
    header = PAYLOAD_HEADER_STRUCT.pack(len(blob), num_blocks, len(fname))
    body = header * PAYLOAD_HEADER_REDUNDANCY + fname + blob
    return body.ljust(num_blocks * block_size, b"\x00"), num_blocks


def interleaved_length(blob_len: int, name_len: int, ecc_symbols: int) -> int:
    block_size = effective_block_size(ecc_symbols)
    raw_len = PAYLOAD_HEADER_STRUCT.size * PAYLOAD_HEADER_REDUNDANCY + name_len + blob_len
    num_blocks = max(1, int(math.ceil(raw_len / block_size)))
    return num_blocks * (block_size + ecc_symbols)


def parse_frame(data: bytes) -> tuple[bytes, str]:
    size = PAYLOAD_HEADER_STRUCT.size
    copies = [data[index * size:(index + 1) * size] for index in range(PAYLOAD_HEADER_REDUNDANCY)]
    if any(len(copy) != size for copy in copies):
        raise ValueError("payload header is truncated")
    blob_len, _num_blocks, name_len = PAYLOAD_HEADER_STRUCT.unpack(_majority(copies))
    start = size * PAYLOAD_HEADER_REDUNDANCY
    fname = data[start:start + name_len]
    blob = data[start + name_len:start + name_len + blob_len]
    if len(blob) != blob_len:
        raise ValueError("encrypted blob is truncated")
    return blob, fname.decode("utf-8", errors="replace")


def _majority(copies: list[bytes]) -> bytes:
    width = len(copies[0])
    out = bytearray(width)
    for index in range(width):
        votes = [copy[index] for copy in copies]
        out[index] = max(set(votes), key=votes.count)
    return bytes(out)
