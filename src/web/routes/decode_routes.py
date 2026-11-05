from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from web.decode_bodies import DecodeRequest, SessionCreate, SessionSetup
from web.decode_task import capture_task, decode_task
from web.safe import safe_segment, under_data
from web.scan_upload import store_upload
from web.session_rows import session_rows
from web.tasks import submit
from web.wizard_keep import keep_named
from web.wizard_logic import apply_setup, note_file, open_session, session_path
from web.wizard_present import present

router = APIRouter()


@router.get("/decode/sessions")
def sessions() -> list[dict[str, object]]:
    return session_rows()


@router.post("/decode/sessions")
def create_session(body: SessionCreate) -> dict[str, object]:
    return open_session(body.duplex, body.print_job_id or "")


@router.get("/decode/sessions/{job_id}")
def session(job_id: str) -> dict[str, object]:
    require_session(job_id)
    return present(job_id)


@router.post("/decode/sessions/{job_id}/setup")
def setup(job_id: str, body: SessionSetup) -> dict[str, object]:
    require_session(job_id)
    return apply_setup(job_id, body.duplex, body.print_job_id)


@router.post("/decode/sessions/{job_id}/capture")
def capture(job_id: str) -> dict[str, str]:
    require_session(job_id)
    return {"task_id": submit(capture_task(job_id))}


@router.post("/decode/sessions/{job_id}/upload")
def upload(job_id: str, files: list[UploadFile] = File()) -> dict[str, object]:
    folder = require_session(job_id)
    for item in files:
        note_file(job_id, store_upload(folder, item))
    return present(job_id)


@router.delete("/decode/sessions/{job_id}/scans/{name}")
def remove_scan(job_id: str, name: str) -> dict[str, str]:
    folder = require_session(job_id)
    path = under_data(folder / "scans" / safe_segment(name))
    if not path.is_file():
        raise HTTPException(404, "Scan not found")
    path.unlink()
    return {"message": "Removed"}


@router.post("/decode/sessions/{job_id}/scans/{name}/keep")
def keep_scan(job_id: str, name: str) -> dict[str, object]:
    require_session(job_id)
    return keep_named(job_id, safe_segment(name))


@router.post("/decode/sessions/{job_id}/decode")
def decode(job_id: str, body: DecodeRequest) -> dict[str, str]:
    require_session(job_id)
    return {"task_id": submit(decode_task(job_id, body))}


def require_session(job_id: str) -> Path:
    folder = session_path(job_id)
    if not folder.is_dir():
        raise HTTPException(404, "Scan session not found")
    return folder
