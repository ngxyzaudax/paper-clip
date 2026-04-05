from __future__ import annotations

from pathlib import Path
from typing import Callable

from common.config import ALGO_FIELDS, PaperClipConfig, FLAG_ENCRYPTED
from common.data_store import create_job, digital_dir
from common.page_layout import pages_needed
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
    flags = FLAG_ENCRYPTED if passphrase else 0
    raw_data = input_path.read_bytes()
    payload, _ = prepare_payload(
        raw_data, config, filename=input_path.name, passphrase=passphrase,
    )
    data_pages = pages_needed(len(payload), config)
    total_pages = data_pages + config.redundancy_pages
    config_dict = {k: getattr(config, k) for k in ALGO_FIELDS}
    for k in (
        "margin_top_mm",
        "margin_right_mm",
        "margin_bottom_mm",
        "margin_left_mm",
    ):
        config_dict[k] = getattr(config, k)
    job_dir = create_job(input_path.name, "inline", config_dict, total_pages)
    output_base = digital_dir(job_dir) / "page"
    png_paths = encode(
        input_path, output_base, config,
        on_page_complete=on_page_complete, flags=flags, passphrase=passphrase,
    )
    return str(job_dir), png_paths
