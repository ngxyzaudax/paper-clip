from collections.abc import Callable
from dataclasses import asdict
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile
from pydantic import BaseModel, Field

from common.config import PaperClipConfig
from serialization.encode.frame_payload import PreparedPayload
from web.inbox_store import UploadTooLarge, inbox_file, save_upload
from web.preview_cache import matching_encode, render_preview, request_key
from web.tasks import TaskRecord, push, submit
from workflows.encode_job import OnPageComplete, create_encode_job, render_encode_job
from workflows.encode_picks import PickValue, option_catalog
from workflows.encode_plan import build_plan
from workflows.encoding_form import EncodingFormPicks, default_encoding_form_picks, profile_source, sheet_plan
from workflows.picks_parse import picks_from_dict

router = APIRouter()


class PreviewBody(BaseModel):
    file_id: str | None = None
    picks: dict[str, PickValue | None] = Field(default_factory=dict)
    page: int = 0
    passphrase: str | None = None


class EncodeBody(PreviewBody):
    preview_id: str | None = None


@router.get("/encode/options")
def encode_options() -> dict[str, object]:
    picks = default_encoding_form_picks()
    return {"fields": option_catalog(), "defaults": asdict(picks), "profile": profile_source(picks)}


@router.post("/inbox")
def inbox(file: UploadFile) -> dict[str, object]:
    try:
        return save_upload(file.filename or "file.bin", file.file)
    except UploadTooLarge as exc:
        raise HTTPException(413, str(exc)) from exc


@router.post("/encode/preview")
def encode_preview(body: PreviewBody) -> dict[str, object]:
    path = inbox_file(body.file_id) if body.file_id else None
    raw, name = (path.read_bytes(), path.name) if path else (None, "")
    return render_preview(body.file_id, picks_from_dict(body.picks), body.page, body.passphrase or None, raw, name)


@router.post("/encode")
def encode_job(body: EncodeBody) -> dict[str, str]:
    if not body.file_id:
        raise HTTPException(400, "Choose a file to encode")
    path = inbox_file(body.file_id)
    picks = picks_from_dict(body.picks)
    return {"task_id": submit(_encode_task(body, path, picks))}


def _encode_task(body: EncodeBody, path: Path, picks: EncodingFormPicks) -> Callable[[TaskRecord], dict[str, object]]:
    def run(record: TaskRecord) -> dict[str, object]:
        config, prepared = _prepared(body, path, picks)
        job_dir = create_encode_job(config, path.name, prepared, sheet_plan(picks).sides)
        paths = render_encode_job(job_dir, config, path, body.passphrase or None, prepared, on_page_complete=_page_events(record, job_dir.name))
        return {"job_id": job_dir.name, "pages": len(paths), "message": f"Encoded {len(paths)} page(s)"}
    return run


def _prepared(body: EncodeBody, path: Path, picks: EncodingFormPicks) -> tuple[PaperClipConfig, PreparedPayload]:
    cached = matching_encode(body.preview_id or "", request_key(body.file_id, picks, body.passphrase or None))
    if cached is not None and cached.prepared is not None:
        return cached.config, cached.prepared
    prepared, config, _plan = build_plan(path.read_bytes(), path.name, picks, body.passphrase or None)
    return config, prepared


def _page_events(record: TaskRecord, job_id: str) -> OnPageComplete:
    def on_page(index: int, total: int, page: Path | None) -> None:
        push(record, "progress", {"fraction": (index + 1) / max(total, 1), "label": f"Page {index + 1}/{total}"})
        if page is not None:
            push(record, "page", {"url": f"/api/artifacts/print/{job_id}/{page.name}?size=320", "label": f"Page {index + 1}"})
    return on_page
