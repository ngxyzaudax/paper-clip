import hashlib
import uuid
from pathlib import Path
from typing import BinaryIO

from common.data_store import DATA_ROOT
from common.decode_output import safe_filename
from web.safe import safe_segment, under_data

INBOX = DATA_ROOT / "inbox"
UPLOAD_CHUNK = 1024 * 1024
MAX_UPLOAD_BYTES = 512 * 1024 * 1024


class UploadTooLarge(ValueError):
    """Raised when an upload exceeds MAX_UPLOAD_BYTES."""


class EmptyUpload(ValueError):
    """Raised when an upload carries no bytes."""


def save_upload(name: str, stream: BinaryIO, limit: int = MAX_UPLOAD_BYTES) -> dict[str, object]:
    """Stream an upload into a fresh inbox folder and return its id, name, size, and digest."""
    file_id = uuid.uuid4().hex
    dest = INBOX / file_id / safe_filename(name)
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        size, digest = _copy(stream, dest, limit)
    except ValueError:
        _discard(dest)
        raise
    return {"file_id": file_id, "name": dest.name, "size": size, "sha256": digest}


def inbox_file(file_id: str) -> Path:
    """Return the single file stored under an inbox id, refusing ids that leave the inbox."""
    folder = under_data(INBOX / safe_segment(file_id))
    files = [path for path in folder.iterdir() if path.is_file()] if folder.is_dir() else []
    if len(files) != 1:
        raise FileNotFoundError(file_id)
    return files[0]


def _copy(stream: BinaryIO, dest: Path, limit: int) -> tuple[int, str]:
    digest = hashlib.sha256()
    size = 0
    with dest.open("wb") as handle:
        while chunk := stream.read(UPLOAD_CHUNK):
            size += len(chunk)
            if size > limit:
                raise UploadTooLarge(f"Upload exceeds {limit // (1024 * 1024)} MB")
            handle.write(chunk)
            digest.update(chunk)
    if size == 0:
        raise EmptyUpload("Choose a file to encode")
    return size, digest.hexdigest()


def _discard(dest: Path) -> None:
    dest.unlink(missing_ok=True)
    dest.parent.rmdir()
