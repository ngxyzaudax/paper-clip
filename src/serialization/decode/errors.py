from typing import Any

from serialization.encode.qr_header import DecodedQrHeader


class DecodeError(Exception):
    """A scan could not be turned back into the original file."""


class PassphraseError(DecodeError):
    """The data survived, but the passphrase is missing or wrong."""


class LostDocument(DecodeError):
    """The QR header identified the document, but its data could no longer be recovered."""

    def __init__(
        self, message: str, header: DecodedQrHeader, scanned: tuple[int, ...], observed: tuple[Any, ...] = (),
    ) -> None:
        super().__init__(message)
        self.header = header
        self.scanned = scanned
        self.observed = observed
