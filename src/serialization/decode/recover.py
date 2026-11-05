from typing import NamedTuple

from common.codec import effective_block_size
from common.compression import decompress
from common.crypto import compute_sha256
from common.encryption import DEFAULT_ENCRYPTION_PASSPHRASE, decrypt
from common.format_spec import FLAG_USER_PASSPHRASE
from serialization.decode.errors import DecodeError, PassphraseError
from serialization.decode.repair import StreamRepair, repair_blocks
from serialization.encode.frame_payload import parse_frame
from serialization.encode.qr_header import DecodedQrHeader


class Recovered(NamedTuple):
    raw: bytes
    filename: str
    repair: StreamRepair


def recover_stream(
    payload: bytes,
    header: DecodedQrHeader,
    erasures: list[int],
    passphrase: str | None,
) -> Recovered:
    block_size = effective_block_size(header.ecc_sym)
    codeword = block_size + header.ecc_sym
    if codeword <= 0 or len(payload) % codeword != 0:
        raise DecodeError("payload length is not a whole number of Reed-Solomon codewords")
    num_blocks = len(payload) // codeword
    framed, repair = repair_blocks(payload, num_blocks, codeword, header.ecc_sym, erasures)
    blob, filename = _frame(framed)
    raw = _open(blob, header, passphrase)
    _check(raw, header)
    return Recovered(raw, filename, repair)


def _frame(framed: bytes) -> tuple[bytes, str]:
    try:
        return parse_frame(framed)
    except ValueError as exc:
        raise DecodeError(str(exc)) from exc


def _open(blob: bytes, header: DecodedQrHeader, passphrase: str | None) -> bytes:
    key = _passphrase(header.flags, passphrase)
    try:
        return decompress(decrypt(blob, key))
    except Exception as exc:
        raise _open_error(header) from exc


def _open_error(header: DecodedQrHeader) -> DecodeError:
    if header.flags & FLAG_USER_PASSPHRASE:
        return PassphraseError("decryption or decompression failed: the passphrase is wrong")
    return DecodeError("decryption or decompression failed")


def _check(raw: bytes, header: DecodedQrHeader) -> None:
    if len(raw) != header.original_length:
        raise DecodeError(
            f"original length mismatch: recovered {len(raw)} bytes, header says {header.original_length}"
        )
    if compute_sha256(raw) != header.original_sha256:
        raise DecodeError("SHA-256 of the recovered file does not match the QR header")


def _passphrase(flags: int, passphrase: str | None) -> str:
    if not flags & FLAG_USER_PASSPHRASE:
        return DEFAULT_ENCRYPTION_PASSPHRASE
    if not passphrase:
        raise PassphraseError("this page was encrypted with a user passphrase")
    return passphrase
