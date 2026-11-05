import json
from pathlib import Path
from typing import Callable

from common.config import ALGO_FIELDS, PaperClipConfig
from common.data_store import create_print_job, digital_dir
from common.page_layout import data_capacity_bytes, pages_needed
from common.paper_sizes import detect_paper_size
from serialization.encode.frame_payload import PreparedPayload
from serialization.encode.parity_render import OnPageImage
from serialization.encode.pipeline import encode

OnPageComplete = Callable[[int, int, Path | None], None]
LAYOUT_FIELDS = (
    "margin_top_mm",
    "margin_right_mm",
    "margin_bottom_mm",
    "margin_left_mm",
    "page_width_mm",
    "page_height_mm",
)


def run_encode_job(
    config: PaperClipConfig,
    input_path: Path,
    passphrase: str | None,
    prepared: PreparedPayload,
    on_page_image: OnPageImage | None = None,
    on_page_complete: OnPageComplete | None = None,
    sides: int = 1,
) -> tuple[Path, list[Path]]:
    job_dir = create_encode_job(config, input_path.name, prepared, sides)
    return job_dir, render_encode_job(job_dir, config, input_path, passphrase, prepared, on_page_image, on_page_complete)


def render_encode_job(
    job_dir: Path,
    config: PaperClipConfig,
    input_path: Path,
    passphrase: str | None,
    prepared: PreparedPayload,
    on_page_image: OnPageImage | None = None,
    on_page_complete: OnPageComplete | None = None,
) -> list[Path]:
    """Render every page of an encode job into the job's digital folder."""
    return encode(
        input_path,
        digital_dir(job_dir) / "page",
        config,
        on_page_complete=on_page_complete,
        passphrase=passphrase,
        prepared=prepared,
        on_page_image=on_page_image,
        duplex=job_is_duplex(job_dir),
    )


def job_is_duplex(job_dir: Path) -> bool:
    stored = json.loads((job_dir / "job.json").read_text())
    return isinstance(stored, dict) and stored.get("sides") == 2


def create_encode_job(config: PaperClipConfig, filename: str, prepared: PreparedPayload, sides: int) -> Path:
    data_pages = pages_needed(len(prepared.payload), config)
    return create_print_job(
        filename,
        "inline",
        config_record(config),
        data_pages + config.redundancy_pages,
        paper_size=detect_paper_size(config.page_width_mm, config.page_height_mm),
        data_pages=data_pages,
        payload_bytes=len(prepared.payload),
        data_capacity_bytes_per_page=data_capacity_bytes(config),
        original_sha256=prepared.original_sha256.hex(),
        sides=sides,
    )


def config_record(config: PaperClipConfig) -> dict[str, object]:
    return {name: getattr(config, name) for name in (*ALGO_FIELDS, *LAYOUT_FIELDS)}
