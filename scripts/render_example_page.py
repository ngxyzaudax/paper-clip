import argparse
from pathlib import Path

import numpy as np
from PIL import Image

from common.config import PaperClipConfig, default_config
from common.page_capacity import data_capacity_bytes, data_capacity_symbols
from scan_sim.render import render_document
from serialization.decode.pipeline import decode
from serialization.encode.encoder import prepare_payload

from page_annotation import annotate_page, layout_rows

FILENAME = "random.bin"


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a full-capacity page and an annotated copy.")
    parser.add_argument("--out", type=Path, default=Path("/opt/cursor/artifacts"))
    parser.add_argument("--seed", type=int, default=8603)
    args = parser.parse_args()
    config = default_config()
    rng = np.random.default_rng(args.seed)
    stream = rng.integers(0, 256, size=data_capacity_bytes(config), dtype=np.uint8).tobytes()
    size = max_random_payload(stream, config)
    payload = stream[:size]
    images, _prepared, _grids = render_document(payload, config, filename=FILENAME)
    page = images[0]
    args.out.mkdir(parents=True, exist_ok=True)
    page_path = args.out / "a4_full_capacity_page.png"
    annotated_path = args.out / "a4_full_capacity_annotated.png"
    Image.fromarray(page).save(page_path, dpi=(config.print_dpi, config.print_dpi))
    annotate_page(page, config).save(annotated_path)
    recovered, name = decode(page, use_model=False)
    _report(config, size, recovered == payload and name == FILENAME, page_path, annotated_path)


def max_random_payload(stream: bytes, config: PaperClipConfig) -> int:
    capacity = data_capacity_bytes(config)
    low, high = 0, len(stream)
    while low < high:
        middle = (low + high + 1) // 2
        if len(prepare_payload(stream[:middle], config, FILENAME).payload) <= capacity:
            low = middle
        else:
            high = middle - 1
    return low


def _report(config: PaperClipConfig, size: int, decoded: bool, *paths: Path) -> None:
    print(f"data cells      {data_capacity_symbols(config)}")
    print(f"capacity bytes  {data_capacity_bytes(config)}")
    print(f"max raw random  {size}")
    print(f"decodes         {decoded}")
    for label, value in layout_rows(config):
        print(f"{label:<15} {value}")
    for path in paths:
        print(f"wrote           {path}")


if __name__ == "__main__":
    main()
