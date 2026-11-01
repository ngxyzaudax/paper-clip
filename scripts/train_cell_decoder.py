import sys
from pathlib import Path

import numpy as np

from ml.train import train_cell_decoder
from ml.train_real import train_on_pages
from ml.scan_grid import write_page_examples


def main() -> None:
    if len(sys.argv) == 1:
        path, accuracy = train_cell_decoder()
        print(f"saved {path} held-out accuracy {accuracy:.3f}")
        return
    if len(sys.argv) != 3:
        raise SystemExit("usage: train_cell_decoder.py [SCAN_DIR DIGITAL_DIR]")
    scan_dir, digital_dir = Path(sys.argv[1]), Path(sys.argv[2])
    destination = Path("data") / "training" / scan_dir.name
    pages = write_page_examples(scan_dir, digital_dir, destination)
    for page in pages:
        labelled = int(np.sum(page.labels >= 0))
        print(
            f"page {page.page_index + 1}: {page.image.shape[1]}x{page.image.shape[0]} "
            f"{labelled} labelled cells, colour agreement {page.agreement:.3f}",
            flush=True,
        )
    path, accuracy = train_on_pages(pages)
    print(f"saved {path} held-out accuracy {accuracy:.3f}")


if __name__ == "__main__":
    main()
