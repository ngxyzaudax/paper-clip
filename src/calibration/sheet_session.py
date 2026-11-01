import shutil
from datetime import datetime
from pathlib import Path

from calibration.profile import profile_density, save_density_profile
from calibration.scan_record import ScanRecord, all_reads, records_in, scan_record
from calibration.sheet_io import calibration_dir, session_dir
from calibration.sheet_limits import ChosenProfile, choose_profile
from calibration.sheet_score import PatchRead
from common.config import PaperClipConfig, resolve_config


def score_paths(paths: list[Path]) -> tuple[PatchRead, ...]:
    return all_reads(tuple(record for path in paths for record in _records(path)))


def session_records() -> tuple[ScanRecord, ...]:
    return records_in(session_dir())


def chosen_config(chosen: ChosenProfile) -> PaperClipConfig:
    return resolve_config(
        cell_size_px=chosen.cell_size_px,
        num_symbols=chosen.num_symbols,
        tag_size_mm=chosen.tag_size_mm,
        tag_pitch_mm=chosen.tag_pitch_mm,
        qr_module_mm=chosen.qr_module_mm,
        dot_ratio=chosen.dot_ratio,
        print_dpi=720,
    )


def save_chosen(reads: tuple[PatchRead, ...]) -> ChosenProfile:
    chosen = choose_profile(reads)
    config = chosen_config(chosen)
    save_density_profile(config, profile_density(config))
    return chosen


def next_scan_path() -> Path:
    folder = session_dir()
    folder.mkdir(parents=True, exist_ok=True)
    numbers = [int(path.stem.rsplit("-", 1)[-1]) for path in folder.glob("scan-*.png") if path.stem[5:].isdigit()]
    return folder / f"scan-{max(numbers, default=0) + 1:02d}.png"


def archive_session() -> Path | None:
    """Move the current session aside so the next scans start a fresh set of reads."""
    folder = session_dir()
    if not folder.exists() or not any(folder.iterdir()):
        return None
    target = calibration_dir() / "archive" / datetime.now().strftime("session-%Y%m%d-%H%M%S")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(folder), str(target))
    return target


def _records(path: Path) -> tuple[ScanRecord, ...]:
    if path.is_dir():
        return records_in(path)
    return (scan_record(path),) if path.exists() else ()
