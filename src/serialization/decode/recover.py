from common.codec import deinterleave_blocks, effective_block_size, rs_decode_block
from common.compression import decompress
from common.crypto import compute_sha256
from common.encryption import DEFAULT_ENCRYPTION_PASSPHRASE, decrypt
from common.format_spec import FLAG_USER_PASSPHRASE
from serialization.decode.errors import DecodeError
from serialization.encode.frame_payload import parse_frame
from serialization.encode.qr_header import DecodedQrHeader


def recover_stream(
    payload: bytes,
    header: DecodedQrHeader,
    erasures: list[int],
    passphrase: str | None,
) -> tuple[bytes, str]:
    block_size = effective_block_size(header.ecc_sym)
    codeword = block_size + header.ecc_sym
    if codeword <= 0 or len(payload) % codeword != 0:
        raise DecodeError("payload length is not a whole number of Reed-Solomon codewords")
    num_blocks = len(payload) // codeword
    framed = _decode_blocks(payload, num_blocks, codeword, header.ecc_sym, erasures)
    try:
        blob, filename = parse_frame(framed)
    except ValueError as exc:
        raise DecodeError(str(exc)) from exc
    try:
        compressed = decrypt(blob, _passphrase(header.flags, passphrase))
        raw = decompress(compressed)
    except DecodeError:
        raise
    except Exception as exc:
        raise DecodeError("decryption or decompression failed") from exc
    if len(raw) != header.original_length:
        raise DecodeError(
            f"original length mismatch: recovered {len(raw)} bytes, header says {header.original_length}"
        )
    digest = compute_sha256(raw)
    if digest != header.original_sha256:
        raise DecodeError("SHA-256 of the recovered file does not match the QR header")
    return raw, filename


def _decode_blocks(
    payload: bytes, num_blocks: int, codeword: int, ecc_symbols: int, erasures: list[int],
) -> bytes:
    blocks = deinterleave_blocks(payload, num_blocks, codeword)
    decoded: list[bytes] = []
    for index, block in enumerate(blocks):
        erase = sorted({
            pos // num_blocks
            for pos in erasures
            if pos % num_blocks == index and 0 <= pos // num_blocks < codeword
        })
        try:
            decoded.append(rs_decode_block(block, ecc_symbols, erase or None))
        except Exception as exc:
            raise DecodeError(
                f"Reed-Solomon decode failed with {len(erasures)} erasures: {exc}"
            ) from exc
    return b"".join(decoded)


def _passphrase(flags: int, passphrase: str | None) -> str:
    if passphrase:
        return passphrase
    if flags & FLAG_USER_PASSPHRASE:
        raise DecodeError("this page was encrypted with a user passphrase")
    return DEFAULT_ENCRYPTION_PASSPHRASE
