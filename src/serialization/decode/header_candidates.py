import json
from dataclasses import replace
from pathlib import Path

from common.config import PaperClipConfig, config_from_job_dict, default_config, validate_config
from common.data_store import PRINT_JOBS_DIR
from serialization.decode.header_config import config_from_header
from serialization.encode.header_bytes import DecodedQrHeader

_JOB_LIMIT = 8


def candidate_configs(hints: tuple[DecodedQrHeader, ...]) -> tuple[PaperClipConfig, ...]:
    found = [config_from_header(header) for header in hints]
    found.extend(stored_configs())
    return _dedupe(found)


def stored_configs() -> tuple[PaperClipConfig, ...]:
    return _dedupe([*_jobs(), *_profile()])


def _jobs() -> tuple[PaperClipConfig, ...]:
    if not PRINT_JOBS_DIR.is_dir():
        return ()
    paths = sorted(PRINT_JOBS_DIR.glob("*/job.json"), key=lambda path: path.stat().st_mtime, reverse=True)
    found: list[PaperClipConfig] = []
    for path in paths[:_JOB_LIMIT]:
        config = _job(path)
        if config is not None:
            found.append(config)
    return tuple(found)


def _job(path: Path) -> PaperClipConfig | None:
    try:
        stored = json.loads(path.read_text()).get("config")
        if isinstance(stored, dict):
            return config_from_job_dict(stored)
    except (OSError, json.JSONDecodeError, ValueError, TypeError):
        return None
    return None


def _profile() -> tuple[PaperClipConfig, ...]:
    from calibration.profile import load_density_profile
    saved = load_density_profile()
    if saved is None:
        return ()
    try:
        return (validate_config(replace(
            default_config(),
            cell_size_px=saved.cell_size_px,
            num_symbols=saved.num_symbols,
            tag_size_mm=saved.tag_size_mm,
            tag_pitch_mm=saved.tag_pitch_mm,
            print_dpi=saved.print_dpi,
            qr_module_mm=saved.qr_module_mm,
            dot_ratio=saved.dot_ratio,
        )),)
    except (TypeError, ValueError):
        return ()


def _dedupe(configs: list[PaperClipConfig]) -> tuple[PaperClipConfig, ...]:
    found: list[PaperClipConfig] = []
    seen: set[tuple[object, ...]] = set()
    for config in configs:
        key = _key(config)
        if key in seen:
            continue
        seen.add(key)
        found.append(config)
    return tuple(found)


def _key(config: PaperClipConfig) -> tuple[object, ...]:
    return (
        config.num_symbols,
        config.cell_size_px,
        config.print_dpi,
        int(round(config.tag_pitch_mm)),
        int(round(config.tag_size_mm * 100)),
        int(round(config.page_width_mm * 100)),
        int(round(config.page_height_mm * 100)),
        int(round(config.margin_top_mm * 100)),
        int(round(config.margin_right_mm * 100)),
        int(round(config.margin_bottom_mm * 100)),
        int(round(config.margin_left_mm * 100)),
        int(round(config.qr_module_mm * 100)),
        int(round(config.dot_ratio * 100)),
    )
