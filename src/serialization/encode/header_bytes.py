import zlib
from typing import NamedTuple

from common.config import PaperClipConfig
from common.dot_ratio import pack_cell_field, unpack_cell_field
from common.format_spec import HEADER_BODY, HEADER_STRUCT, MAGIC
from common.geometry_measure import hundredths_to_mm, mm_to_hundredths
from common.page_layout import grid_dimensions


class DecodedQrHeader(NamedTuple):
    tag_pitch_mm: int
    flags: int
    num_symbols: int
    cell_size_px: int
    ecc_sym: int
    print_dpi: int
    margin_top_mm: float
    margin_right_mm: float
    margin_bottom_mm: float
    margin_left_mm: float
    page_width_mm: float
    page_height_mm: float
    cols: int
    rows: int
    page_index: int
    total_pages: int
    data_pages: int
    payload_length: int
    original_length: int
    original_sha256: bytes
    dot_ratio: float


def encode_header_bytes(
    config: PaperClipConfig,
    page_index: int,
    total_pages: int,
    data_pages: int,
    payload_length: int,
    original_length: int,
    original_sha256: bytes,
    flags: int,
) -> bytes:
    cols, rows = grid_dimensions(config)
    body = HEADER_BODY.pack(
        MAGIC,
        int(round(config.tag_pitch_mm)),
        flags,
        config.num_symbols,
        pack_cell_field(config.cell_size_px, config.dot_ratio),
        config.ecc_sym,
        config.print_dpi,
        mm_to_hundredths(config.margin_top_mm),
        mm_to_hundredths(config.margin_right_mm),
        mm_to_hundredths(config.margin_bottom_mm),
        mm_to_hundredths(config.margin_left_mm),
        mm_to_hundredths(config.page_width_mm),
        mm_to_hundredths(config.page_height_mm),
        cols,
        rows,
        page_index,
        total_pages,
        data_pages,
        payload_length,
        original_length,
        original_sha256,
    )
    return body + (zlib.crc32(body) & 0xFFFFFFFF).to_bytes(4, "big")


def decode_header_bytes(blob: bytes) -> DecodedQrHeader:
    if len(blob) != HEADER_STRUCT.size:
        raise ValueError("invalid header length")
    unpacked = HEADER_STRUCT.unpack(blob)
    if unpacked[0] != MAGIC:
        raise ValueError("invalid header magic")
    crc = unpacked[-1]
    if (zlib.crc32(blob[:-4]) & 0xFFFFFFFF) != crc:
        raise ValueError("invalid header crc")
    cell_px, dot_ratio = unpack_cell_field(unpacked[4])
    return DecodedQrHeader(
        tag_pitch_mm=unpacked[1],
        flags=unpacked[2],
        num_symbols=unpacked[3],
        cell_size_px=cell_px,
        ecc_sym=unpacked[5],
        print_dpi=unpacked[6],
        margin_top_mm=hundredths_to_mm(unpacked[7]),
        margin_right_mm=hundredths_to_mm(unpacked[8]),
        margin_bottom_mm=hundredths_to_mm(unpacked[9]),
        margin_left_mm=hundredths_to_mm(unpacked[10]),
        page_width_mm=hundredths_to_mm(unpacked[11]),
        page_height_mm=hundredths_to_mm(unpacked[12]),
        cols=unpacked[13],
        rows=unpacked[14],
        page_index=unpacked[15],
        total_pages=unpacked[16],
        data_pages=unpacked[17],
        payload_length=unpacked[18],
        original_length=unpacked[19],
        original_sha256=unpacked[20],
        dot_ratio=dot_ratio,
    )
