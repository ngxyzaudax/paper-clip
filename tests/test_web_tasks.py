import time

from web.tasks import TaskRecord, get_task, push, resume_point, stream, submit


def _three_pages(record: TaskRecord) -> dict[str, object]:
    for index in range(3):
        push(record, "page", {"index": index})
    return {"pages": 3}


def _finished(task_id: str) -> TaskRecord:
    for _ in range(100):
        record = get_task(task_id)
        if record and record.state != "running":
            return record
        time.sleep(0.01)
    raise AssertionError(task_id)


def test_stream_numbers_every_event_and_resumes_after_the_last_seen_id() -> None:
    record = _finished(submit(_three_pages))
    frames = list(stream(record))
    assert [frame.split("\n")[0] for frame in frames] == ["id: 1", "id: 2", "id: 3", "id: 4"]
    resumed = list(stream(record, resume_point("2")))
    assert len(resumed) == 2
    assert '"index": 2' in resumed[0]
    assert "event: done" in resumed[1]


def test_resume_point_ignores_malformed_ids() -> None:
    assert resume_point(None) == 0
    assert resume_point("x1") == 0
    assert resume_point("7") == 7
