from pathlib import Path

from common.data_store import DATA_ROOT

DECODED_DIR = DATA_ROOT / "decoded"


def safe_filename(filename: str) -> str:
    """The recovered name without any directory part, so a page cannot write outside the target folder."""
    name = Path(filename.replace("\\", "/")).name.strip()
    return name if name not in ("", ".", "..") else "recovered.bin"


def free_path(path: Path) -> Path:
    """`path` when it is unused, otherwise the first `name (n).ext` that is."""
    if not path.exists():
        return path
    counter = 1
    while (candidate := path.with_name(f"{path.stem} ({counter}){path.suffix}")).exists():
        counter += 1
    return candidate


def decode_destination(output: Path | None, filename: str, force: bool) -> Path:
    name = safe_filename(filename)
    if output is None:
        target = Path.cwd() / name
    elif output.is_dir():
        target = output / name
    else:
        target = output
    return target if force else free_path(target)


def job_destination(job_id: str, filename: str) -> Path:
    return free_path(DECODED_DIR / job_id / safe_filename(filename))


def write_recovered(target: Path, raw: bytes) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
    return target
