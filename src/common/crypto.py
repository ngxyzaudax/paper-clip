import hashlib


def compute_sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def verify_sha256(data: bytes, expected: bytes) -> bool:
    return compute_sha256(data) == expected
