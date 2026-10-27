import os

import pytest
from reedsolo import ReedSolomonError

from common.codec import calculate_ecc_symbols, deinterleave_blocks, interleave_blocks, rs_decode_block, rs_encode_block
from common.config import BLOCK_SIZE, resolve_config
from common.fountain import encode_parity_pages, reconstruct_missing
from serialization.decode.errors import DecodeError
from serialization.decode.recover import recover_stream
from serialization.encode.encoder import prepare_payload
from serialization.encode.qr_header import DecodedQrHeader


def _header(prepared, config, flags: int = 0) -> DecodedQrHeader:
    from serialization.encode.qr_header import encode_header_bytes, decode_header_bytes

    blob = encode_header_bytes(
        config, 0, 1, 1, len(prepared.payload), prepared.original_length,
        prepared.original_sha256, flags,
    )
    return decode_header_bytes(blob)


def test_rs_interleave_roundtrip_and_erasures() -> None:
    ecc = 8
    blocks = [os.urandom(40) for _ in range(3)]
    encoded = [rs_encode_block(block, ecc) for block in blocks]
    stream = interleave_blocks(encoded)
    restored = [rs_decode_block(block, ecc) for block in deinterleave_blocks(stream, 3, len(encoded[0]))]
    assert restored == blocks
    mutated = bytearray(stream)
    mutated[0] ^= 0xFF
    mutated[3] ^= 0xFF
    damaged = deinterleave_blocks(bytes(mutated), 3, len(encoded[0]))
    fixed = rs_decode_block(damaged[0], ecc, [0, 1])
    assert fixed == blocks[0]


def test_payload_frame_survives_rs_and_checks_hash() -> None:
    config = resolve_config(paper_size="A6", print_dpi=360, cell_size_px=18, margin_mm=10)
    raw = os.urandom(120)
    prepared = prepare_payload(raw, config, "round.bin", None)
    recovered, name = recover_stream(prepared.payload, _header(prepared, config), [], None)
    assert name == "round.bin"
    assert recovered == raw


def test_user_passphrase_is_required() -> None:
    config = resolve_config(paper_size="A6", print_dpi=360, cell_size_px=18, margin_mm=10)
    raw = b"secret-bytes"
    prepared = prepare_payload(raw, config, "secret.bin", "correct horse")
    header = _header(prepared, config, prepared.flags)
    with pytest.raises(DecodeError):
        recover_stream(prepared.payload, header, [], None)
    recovered, name = recover_stream(prepared.payload, header, [], "correct horse")
    assert recovered == raw
    assert name == "secret.bin"


def test_page_parity_rebuilds_a_missing_page() -> None:
    pages = [os.urandom(32), os.urandom(32), os.urandom(16)]
    parity = encode_parity_pages(pages, 1)
    slots = [pages[0], None, pages[2], parity[0]]
    restored = reconstruct_missing(slots, 3, 1)
    assert restored[0] == pages[0]
    assert restored[1] == pages[1]
    assert restored[2][:16] == pages[2]


def test_too_many_errors_raise() -> None:
    ecc = calculate_ecc_symbols(BLOCK_SIZE, 0.2)
    block = os.urandom(40)
    encoded = bytearray(rs_encode_block(block, ecc))
    for index in range(0, ecc + 4):
        encoded[index] ^= 0xFF
    with pytest.raises(ReedSolomonError):
        rs_decode_block(bytes(encoded), ecc)
