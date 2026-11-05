from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import StreamingResponse

from web.library_index import library_detail, library_index
from web.tasks import get_task, resume_point, snapshot, stream
from workflows.home_status import home_snapshot

router = APIRouter()


@router.get("/home")
def home() -> dict[str, object]:
    return home_snapshot()


@router.get("/library")
def library() -> dict[str, object]:
    return library_index()


@router.get("/library/{sha}")
def library_one(sha: str) -> dict[str, object]:
    return library_detail(sha)


@router.get("/tasks/{task_id}")
def task_state(task_id: str) -> dict[str, object]:
    record = get_task(task_id)
    if record is None:
        raise HTTPException(404, "Task not found")
    return snapshot(record)


@router.get("/tasks/{task_id}/events")
def task_events(task_id: str, last_event_id: str | None = Header(default=None)) -> StreamingResponse:
    record = get_task(task_id)
    if record is None:
        raise HTTPException(404, "Task not found")
    events = stream(record, resume_point(last_event_id))
    return StreamingResponse(events, media_type="text/event-stream", headers={"Cache-Control": "no-cache"})
