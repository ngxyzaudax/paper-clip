import json
import threading
from pathlib import Path

from starlette.testclient import TestClient

from workflows.scan_jobs import next_scan_path


def session_id(client: TestClient, body: dict[str, object]) -> str:
    response = client.post("/api/decode/sessions", json=body)
    assert response.status_code == 200, response.text
    return str(response.json()["job_id"])


def put_scans(path: Path, scans: list[dict[str, object]]) -> None:
    meta = json.loads(path.read_text())
    meta["wizard"]["scans"] = scans
    path.write_text(json.dumps(meta))


def claim_together(folder: Path, count: int) -> set[str]:
    names: list[str] = []
    errors: list[BaseException] = []
    lock = threading.Lock()

    def claim() -> None:
        try:
            path = next_scan_path(folder)
        except BaseException as exc:
            with lock:
                errors.append(exc)
            return
        with lock:
            names.append(path.name)

    threads = [threading.Thread(target=claim) for _ in range(count)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert errors == []
    return set(names)
