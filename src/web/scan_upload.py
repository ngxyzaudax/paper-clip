import os
import uuid
from pathlib import Path
from typing import BinaryIO

from fastapi import HTTPException, UploadFile
from PIL import Image

from common.data_store import scans_dir
from workflows.scan_jobs import next_scan_path
from workflows.scan_list import SCAN_SUFFIXES

MAX_UPLOAD_BYTES = 200 * 1024 * 1024
UPLOAD_CHUNK_BYTES = 1024 * 1024
_FORMAT_SUFFIX = {"PNG": ".png", "JPEG": ".jpg", "TIFF": ".tif"}


def store_upload(job_dir: Path, upload: UploadFile) -> Path:
    partial = _partial_path(job_dir)
    try:
        _write_capped(partial, upload)
        return _finish(job_dir, partial)
    except Exception:
        _discard(partial)
        raise


def image_suffix(path: Path) -> str:
    suffix = _FORMAT_SUFFIX.get(_format(path), "")
    if suffix not in SCAN_SUFFIXES:
        raise HTTPException(400, "Upload is not a supported image")
    return suffix


def _finish(job_dir: Path, partial: Path) -> Path:
    final = next_scan_path(job_dir, image_suffix(partial))
    try:
        os.replace(partial, final)
    except OSError:
        _discard(final)
        raise
    return final


def _partial_path(job_dir: Path) -> Path:
    return scans_dir(job_dir) / f".upload-{uuid.uuid4().hex}.part"


def _write_capped(path: Path, upload: UploadFile) -> None:
    upload.file.seek(0)
    with path.open("wb") as handle:
        _copy_capped(handle, upload)


def _copy_capped(handle: BinaryIO, upload: UploadFile) -> None:
    total = 0
    while True:
        chunk = upload.file.read(UPLOAD_CHUNK_BYTES)
        if not chunk:
            return
        total = _accept_chunk(handle, chunk, total)


def _accept_chunk(handle: BinaryIO, chunk: bytes, total: int) -> int:
    updated = total + len(chunk)
    if updated > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "Upload exceeds 200 MB")
    handle.write(chunk)
    return updated


def _format(path: Path) -> str:
    try:
        return _verified_format(path)
    except Exception as exc:
        raise HTTPException(400, "Upload is not a supported image") from exc


def _verified_format(path: Path) -> str:
    with Image.open(path) as img:
        fmt = img.format or ""
        img.verify()
        return fmt


def _discard(path: Path) -> None:
    if path.is_file():
        path.unlink()
