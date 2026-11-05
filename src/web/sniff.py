import hashlib
from functools import lru_cache
from pathlib import Path

_TEXT = {".txt", ".json", ".md", ".csv", ".log", ".py"}
TEXT_PREVIEW_BYTES = 262144
HEX_PREVIEW_BYTES = 4096
HASH_CHUNK = 1024 * 1024


def file_meta(path: Path) -> dict[str, object]:
    head = _head(path, TEXT_PREVIEW_BYTES)
    kind = content_type(path.name, head[:16])
    return {
        "name": path.name,
        "size": path.stat().st_size,
        "sha256": file_sha256(path),
        "type": kind,
        "hex": head[:HEX_PREVIEW_BYTES].hex(),
        "text": _text(head, kind, path.suffix.lower()),
    }


def file_sha256(path: Path) -> str:
    """Return the SHA-256 of a file, reusing the digest while its size and mtime are unchanged."""
    stat = path.stat()
    return _digest(str(path.resolve()), stat.st_size, stat.st_mtime_ns)


@lru_cache(maxsize=4096)
def _digest(path: str, _size: int, _mtime_ns: int) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        while chunk := handle.read(HASH_CHUNK):
            digest.update(chunk)
    return digest.hexdigest()


def _head(path: Path, size: int) -> bytes:
    with path.open("rb") as handle:
        return handle.read(size)


def content_type(name: str, header: bytes) -> str:
    if header.startswith(b"\x89PNG"):
        return "image/png"
    if header.startswith(b"\xff\xd8"):
        return "image/jpeg"
    if header.startswith(b"GIF8"):
        return "image/gif"
    if header.startswith(b"RIFF") and header[8:12] == b"WEBP":
        return "image/webp"
    if header.startswith(b"%PDF"):
        return "application/pdf"
    if header.startswith(b"PK\x03\x04"):
        return "application/zip"
    suffix = Path(name).suffix.lower()
    if suffix in (".html", ".htm", ".svg"):
        return "text/plain"
    if suffix in _TEXT:
        return "text/plain"
    if suffix in (".jpg", ".jpeg"):
        return "image/jpeg"
    if suffix == ".png":
        return "image/png"
    return "application/octet-stream"


def _text(raw: bytes, kind: str, suffix: str) -> str | None:
    if kind != "text/plain" and suffix not in _TEXT:
        return None
    return raw.decode("utf-8", errors="replace")
