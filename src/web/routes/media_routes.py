from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, Response

from common.data_store import DATA_ROOT, PRINT_JOBS_DIR, SCAN_JOBS_DIR
from web.archive_index import archive_index, calibration_path
from web.crops import centered_crop_jpeg, crop_jpeg
from web.inbox_store import inbox_file
from web.preview_cache import preview_jpeg
from web.safe import safe_segment, under_data
from web.sniff import content_type, file_meta
from web.thumbs import sized_image

router = APIRouter()


@router.get("/archive")
def archive() -> dict[str, list[dict[str, object]]]:
    return archive_index()


@router.get("/artifacts/{kind}/{ident}/{name}/crop")
def artifact_crop(
    kind: str, ident: str, name: str,
    x: int = 0, y: int = 0, w: int = 64, h: int = 64, fx: float | None = None, fy: float | None = None,
) -> Response:
    path = _artifact(kind, safe_segment(ident), safe_segment(name))
    if fx is not None and fy is not None:
        return Response(centered_crop_jpeg(path, fx, fy, w, h), media_type="image/jpeg")
    return Response(crop_jpeg(path, x, y, w, h), media_type="image/jpeg")


@router.get("/artifacts/{kind}/{ident}/{name}")
def artifact(kind: str, ident: str, name: str, size: int | None = None) -> FileResponse:
    path = _artifact(kind, safe_segment(ident), safe_segment(name))
    return FileResponse(sized_image(path, size))


@router.get("/media/preview/{preview_id}/{name}")
def preview(preview_id: str, name: str) -> FileResponse:
    return FileResponse(preview_jpeg(safe_segment(preview_id), safe_segment(name)))


@router.get("/media/damage/{sha16}/{stamp}/{name}")
def damage(sha16: str, stamp: str, name: str) -> FileResponse:
    path = under_data(DATA_ROOT / "health" / "damage" / safe_segment(sha16) / safe_segment(stamp) / safe_segment(name))
    if not path.is_file():
        raise HTTPException(404, "Image not found")
    return FileResponse(path)


@router.get("/files/inbox/{file_id}")
def inbox_bytes(file_id: str) -> FileResponse:
    path = inbox_file(safe_segment(file_id))
    return _download(path)


@router.get("/files/inbox/{file_id}/meta")
def inbox_meta(file_id: str) -> dict[str, object]:
    return file_meta(inbox_file(safe_segment(file_id)))


@router.get("/files/decoded/{job_id}/{name}")
def decoded_bytes(job_id: str, name: str) -> FileResponse:
    return _download(_decoded(job_id, name))


@router.get("/files/decoded/{job_id}/{name}/meta")
def decoded_meta(job_id: str, name: str) -> dict[str, object]:
    return file_meta(_decoded(job_id, name))


def _artifact(kind: str, ident: str, name: str) -> Path:
    roots = {
        "print": PRINT_JOBS_DIR / ident / "digital" / name,
        "scan": SCAN_JOBS_DIR / ident / "scans" / name,
        "calibration": calibration_path(DATA_ROOT / "calibration", ident, name),
    }
    if kind not in roots:
        raise HTTPException(404, "Unknown artifact")
    path = under_data(roots[kind])
    if not path.is_file():
        raise HTTPException(404, "Image not found")
    return path


def _decoded(job_id: str, name: str) -> Path:
    path = under_data(DATA_ROOT / "decoded" / safe_segment(job_id) / safe_segment(name))
    if not path.is_file():
        raise HTTPException(404, "File not found")
    return path


def _download(path: Path) -> FileResponse:
    kind = content_type(path.name, path.read_bytes()[:16])
    headers = {"X-Content-Type-Options": "nosniff", "Content-Security-Policy": "sandbox"}
    return FileResponse(path, media_type=kind, headers=headers)
