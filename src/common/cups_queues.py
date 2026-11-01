import subprocess
from typing import NamedTuple
from urllib.parse import unquote, urlsplit

from common.types import PrinterInfo


class CupsQueue(NamedTuple):
    name: str
    device_uri: str


def local_queues() -> tuple[CupsQueue, ...]:
    try:
        result = subprocess.run(["lpstat", "-v"], capture_output=True, text=True, check=False)
    except OSError:
        return ()
    if result.returncode != 0:
        return ()
    return tuple(_queue(line) for line in result.stdout.splitlines() if _queue(line) is not None)


def queue_printers(saved_uri: str) -> list[PrinterInfo]:
    return [
        PrinterInfo(queue.name, queue_uri(queue.name), "cups", queue_uri(queue.name) == saved_uri)
        for queue in local_queues()
    ]


def queue_uri(name: str) -> str:
    return f"ipp://localhost:631/printers/{name}"


def queue_name(uri: str) -> str | None:
    parts = urlsplit(uri)
    if parts.hostname not in {"localhost", "127.0.0.1"}:
        return None
    marker = "/printers/"
    if marker not in parts.path:
        return None
    name = unquote(parts.path.rsplit("/", 1)[-1])
    return name or None


def only_queue() -> CupsQueue | None:
    queues = local_queues()
    if len(queues) == 1:
        return queues[0]
    return None


def _queue(line: str) -> CupsQueue | None:
    if not line.startswith("device for "):
        return None
    left, separator, uri = line.partition(": ")
    if not separator or not uri.strip():
        return None
    return CupsQueue(left.removeprefix("device for ").strip(), uri.strip())
