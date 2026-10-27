from __future__ import annotations

from pathlib import Path
from typing import Callable

from common.config import ALGO_FIELDS, PaperClipConfig
from common.data_store import create_print_job, digital_dir
from common.page_layout import data_capacity_bytes, pages_needed
from common.paper_sizes import detect_paper_size
from serialization.encode.encoder import prepare_payload
from serialization.encode.pipeline import encode


def format_encode_success_message(job_dir: str, png_paths: list[Path]) -> str:
    listing = "\n".join(str(p) for p in png_paths)
    return (
        f"[bold green]Complete - {len(png_paths)} page(s):\n{listing}\nJob: {job_dir}[/bold green]"
    )


def run_tui_encode_job(
    *,
    config: PaperClipConfig,
    input_path: Path,
    passphrase: str | None,
    on_page_complete: Callable[[int, int, Path | None], None],
) -> tuple[str, list[Path]]:
    raw_data = input_path.read_bytes()
    prepared = prepare_payload(
        raw_data, config, filename=input_path.name, passphrase=passphrase,
    )
    payload = prepared.payload
    data_pages = pages_needed(len(payload), config)
    total_pages = data_pages + config.redundancy_pages
    config_dict = {k: getattr(config, k) for k in ALGO_FIELDS}
    for k in (
        "margin_top_mm",
        "margin_right_mm",
        "margin_bottom_mm",
        "margin_left_mm",
        "page_width_mm",
        "page_height_mm",
    ):
        config_dict[k] = getattr(config, k)
    job_dir = create_print_job(
        input_path.name, "inline", config_dict, total_pages,
        paper_size=detect_paper_size(config.page_width_mm, config.page_height_mm),
        data_pages=data_pages,
        payload_bytes=len(payload),
        data_capacity_bytes_per_page=data_capacity_bytes(config),
    )
    output_base = digital_dir(job_dir) / "page"
    png_paths = encode(
        input_path, output_base, config,
        on_page_complete=on_page_complete, passphrase=passphrase,
        prepared=prepared,
    )
    return str(job_dir), png_paths
