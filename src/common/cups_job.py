import subprocess
import time
from pathlib import Path

from common.device_error import DeviceError

_FAILED = ("filter failed", "job-completed-with-errors")


def submit_queue_job(queue: str, pdf: Path, title: str, duplex: bool) -> int:
    result = subprocess.run(_command(queue, pdf, title, duplex), capture_output=True, text=True, check=False)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise DeviceError(detail or "the print queue rejected the job")
    return _job_number(result.stdout, queue)


def wait_for_queue_job(queue: str, job_id: int, timeout: float = 900) -> None:
    token = f"{queue}-{job_id}"
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        report = _stanza(queue, token)
        if _failed(report):
            raise DeviceError(f"print job {job_id} was rejected by the print queue")
        if report and token not in _output(["lpstat", "-o", queue]):
            return
        time.sleep(2)
    raise DeviceError(f"print job {job_id} did not finish within {timeout:.0f}s")


def _command(queue: str, pdf: Path, title: str, duplex: bool) -> list[str]:
    sides = "Duplex=DuplexNoTumble" if duplex else "Duplex=None"
    return [
        "lp", "-d", queue, "-t", title,
        "-o", "PageSize=A4",
        "-o", sides,
        "-o", "cupsPrintQuality=High",
        "-o", "ColorModel=RGB",
        "-o", "InputSlot=main",
        "-o", "MediaType=stationery",
        str(pdf),
    ]


def _job_number(text: str, queue: str) -> int:
    prefix = f"{queue}-"
    for token in text.replace("(", " ").split():
        number = token[len(prefix):] if token.startswith(prefix) else ""
        if number.isdigit():
            return int(number)
    raise DeviceError(f"the print queue did not return a job id: {text.strip()}")


def _stanza(queue: str, token: str) -> str:
    lines = _output(["lpstat", "-l", "-W", "all", "-o", queue]).splitlines()
    picked: list[str] = []
    for line in lines:
        if line.startswith(token):
            picked = [line]
            continue
        if picked and line.startswith((" ", "\t")):
            picked.append(line)
        elif picked:
            break
    return "\n".join(picked)


def _failed(report: str) -> bool:
    lowered = report.lower()
    return any(mark in lowered for mark in _FAILED)


def _output(command: list[str]) -> str:
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    return result.stdout
