import json
import logging
import threading
import uuid
from collections import OrderedDict
from collections.abc import Callable, Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

from common.spoken_error import plain_device_message

logger = logging.getLogger(__name__)

KEEP_TASKS = 64
HEARTBEAT_SECONDS = 15.0
_executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix="paper-clip")
_lock = threading.Lock()
_tasks: OrderedDict[str, "TaskRecord"] = OrderedDict()


@dataclass
class TaskRecord:
    id: str
    state: str = "running"
    error: str = ""
    result: dict[str, object] | None = None
    events: list[dict[str, object]] = field(default_factory=list)
    changed: threading.Condition = field(default_factory=threading.Condition)


def submit(work: Callable[[TaskRecord], dict[str, object]]) -> str:
    record = TaskRecord(id=uuid.uuid4().hex)
    with _lock:
        _tasks[record.id] = record
        _evict()
    _executor.submit(_run, record, work)
    return record.id


def get_task(task_id: str) -> TaskRecord | None:
    with _lock:
        return _tasks.get(task_id)


def snapshot(record: TaskRecord) -> dict[str, object]:
    with record.changed:
        return {"task_id": record.id, "state": record.state, "error": record.error, "result": record.result}


def push(record: TaskRecord, event: str, data: dict[str, object]) -> None:
    with record.changed:
        record.events.append({"event": event, "data": data})
        record.changed.notify_all()


def stream(record: TaskRecord, start: int = 0) -> Iterator[str]:
    cursor = max(0, start)
    while True:
        batch, finished = _wait_batch(record, cursor)
        for offset, item in enumerate(batch):
            yield _frame(cursor + offset + 1, str(item["event"]), item["data"])
        cursor += len(batch)
        if finished and not batch:
            return
        if not batch:
            yield ": keep-alive\n\n"


def resume_point(last_event_id: str | None) -> int:
    return int(last_event_id) if last_event_id and last_event_id.isdigit() else 0


def _wait_batch(record: TaskRecord, cursor: int) -> tuple[list[dict[str, object]], bool]:
    with record.changed:
        if cursor >= len(record.events) and record.state == "running":
            record.changed.wait(timeout=HEARTBEAT_SECONDS)
        return list(record.events[cursor:]), record.state != "running"


def _run(record: TaskRecord, work: Callable[[TaskRecord], dict[str, object]]) -> None:
    try:
        _settle(record, "done", work(record))
    except Exception as exc:
        logger.exception("Task %s failed", record.id)
        _settle(record, "error", {"message": plain_device_message(str(exc))})


def _settle(record: TaskRecord, state: str, data: dict[str, object]) -> None:
    with record.changed:
        record.result = data if state == "done" else None
        record.error = "" if state == "done" else str(data.get("message", ""))
        record.state = state
        record.events.append({"event": state, "data": data})
        record.changed.notify_all()


def _evict() -> None:
    finished = [task_id for task_id, task in _tasks.items() if task.state != "running"]
    for task_id in finished[: max(0, len(_tasks) - KEEP_TASKS)]:
        _tasks.pop(task_id, None)


def _frame(event_id: int, event: str, data: object) -> str:
    return f"id: {event_id}\nevent: {event}\ndata: {json.dumps(data)}\n\n"
